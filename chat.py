# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# import os
# from dotenv import load_dotenv
# import google.generativeai as genai

# # Load environment variables
# load_dotenv()
# api_key = os.getenv("GEMINI_API_KEY")

# if not api_key:
#     raise ValueError("❌ GEMINI_API_KEY not found in .env")

# # Configure Gemini with friendly, structured tutor tone
# genai.configure(api_key=api_key)
# model = genai.GenerativeModel(
#     model_name="gemini-1.5-flash",
#     system_instruction="""
# You are Learntendo AI Tutor 🧠📘 — an educational assistant who teaches topics clearly and engagingly.

# ➡️ Always:
# - Use **structured formatting** (headings, bullet points, emojis) to make answers more attractive.
# - Explain with **simple, friendly language** and give relevant **examples**.
# - Keep track of past messages to continue the conversation naturally.

# 🎯 Goal: Make the user feel like they’re learning with a smart, supportive tutor.
# """
# )

# # Initialize in-memory conversation history
# conversation_history = []

# # Set up FastAPI and CORS
# app = FastAPI()

# origins = [
#     "http://localhost",
#     "http://localhost:3000",  # React frontend default
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Request and response schemas
# class ChatRequest(BaseModel):
#     user_input: str

# class ChatResponse(BaseModel):
#     message: str

# @app.post("/chat", response_model=ChatResponse)
# async def chat(request: ChatRequest):
#     user_input = request.user_input.strip()
#     if not user_input:
#         raise HTTPException(status_code=400, detail="Input cannot be empty")

#     try:
#         # Add user message to context
#         conversation_history.append({"role": "user", "parts": [user_input]})

#         # Generate response
#         response = model.generate_content(conversation_history)

#         # Append response to history
#         conversation_history.append({"role": "model", "parts": [response.text]})

#         return ChatResponse(message=response.text)

#     except Exception as e:
#         print("Error:", str(e))
#         raise HTTPException(status_code=500, detail="Error generating response from AI")

# # Start server
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("chat:app", host="0.0.0.0", port=8003, reload=True)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from gtts import gTTS
import google.generativeai as genai
import uuid
import os
import re

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found in .env")

# Configure Gemini with tutor tone
genai.configure(api_key=api_key)
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction="""
You are Learntendo AI Tutor 🧠📘 — an educational assistant who teaches topics clearly and engagingly.

➡️ Always:
- Use **structured formatting** (headings, bullet points, emojis) to make answers more attractive.
- Explain with **simple, friendly language** and give relevant **examples**.
- Keep track of past messages to continue the conversation naturally.

🎯 Goal: Make the user feel like they’re learning with a smart, supportive tutor.
"""
)

# In-memory history
conversation_history = []

# Setup FastAPI
app = FastAPI()

# CORS setup for frontend (e.g., React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatRequest(BaseModel):
    user_input: str

class ChatResponse(BaseModel):
    message: str

# 🧠 Chat endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    user_input = request.user_input.strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="Input cannot be empty")

    try:
        conversation_history.append({"role": "user", "parts": [user_input]})
        response = model.generate_content(conversation_history)
        conversation_history.append({"role": "model", "parts": [response.text]})
        return ChatResponse(message=response.text)

    except Exception as e:
        print("Error:", str(e))
        raise HTTPException(status_code=500, detail="Error generating response from AI")

# 🗣️ Text-to-Speech endpoint
@app.post("/tts", response_class=FileResponse)
async def text_to_speech(request: ChatRequest):
    raw_text = request.user_input.strip()
    if not raw_text:
        raise HTTPException(status_code=400, detail="Input cannot be empty")

    try:
        # Clean and detect language
        clean_text = re.sub(r'[^\w\s.,!?ء-ي]+', '', raw_text)
        language = "ar" if any('\u0600' <= c <= '\u06FF' for c in clean_text) else "en"

        # Generate audio
        tts = gTTS(text=clean_text, lang=language)
        filename = f"audio_{uuid.uuid4()}.mp3"
        filepath = os.path.join(".", filename)
        tts.save(filepath)

        return FileResponse(filepath, media_type="audio/mpeg", filename=filename)

    except Exception as e:
        print("TTS Error:", str(e))
        raise HTTPException(status_code=500, detail="Error generating speech")

# ✅ Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("chat:app", host="0.0.0.0", port=8003, reload=True)
