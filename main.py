# import os
# import json
# import fitz  # PyMuPDF for PDF text extraction
# import docx  # python-docx for DOCX extraction
# from pathlib import Path
# from typing import List, Optional, Union

# from fastapi import FastAPI, UploadFile, Form, File
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from dotenv import load_dotenv
# import google.generativeai as genai
# import uvicorn

# # Load .env file
# load_dotenv()
# API_KEY = os.getenv("gemniKey")

# # Validate API key
# if not API_KEY:
#     raise ValueError("Missing GEMINI_API_KEY in .env")

# # Configure Gemini
# genai.configure(api_key=API_KEY)
# model = genai.GenerativeModel("gemini-1.5-flash")  # ✅ Use the faster model

# # Uploads folder
# UPLOAD_DIR = Path("Uploads")
# UPLOAD_DIR.mkdir(exist_ok=True)

# # FastAPI setup
# app = FastAPI()
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # MCQ Model
# class McqQuestion(BaseModel):
#     questionNumber: int
#     question: str
#     options: List[str]
#     correctAnswer: str
#     explanation: str

# # Extract text from files
# def extract_text_from_file(file_path: str) -> str:
#     ext = file_path.split('.')[-1].lower()
#     try:
#         if ext == "pdf":
#             doc = fitz.open(file_path)
#             return "\n".join(page.get_text("text") for page in doc)
#         elif ext == "docx":
#             doc = docx.Document(file_path)
#             return "\n".join(para.text for para in doc.paragraphs)
#         elif ext == "txt":
#             with open(file_path, "r", encoding="utf-8") as f:
#                 return f.read()
#         else:
#             return ""
#     except Exception as e:
#         print("Error reading file:", e)
#         return ""

# # Main endpoint
# @app.post("/generateQuestions")
# async def generate_questions(
#     sourceType: str = Form(...),
#     textInput: Optional[str] = Form(None),
#     numOfQuestions: int = Form(...),
#     difficultyLevel: str = Form(...),
#     typeOfQuestions: str = Form(...),
#     fileInput: Optional[UploadFile] = File(None)
# ) -> Union[List[McqQuestion], dict]:

#     # Read input text
#     if sourceType == "TEXT":
#         text_source = textInput
#     elif sourceType == "FILE" and fileInput:
#         save_to = UPLOAD_DIR / fileInput.filename
#         with open(save_to, 'wb') as f:
#             f.write(await fileInput.read())
#         text_source = extract_text_from_file(str(save_to))
#         os.remove(save_to)
#         if not text_source.strip():
#             return {"error": "Could not extract text from the file. Ensure it's a readable PDF, DOCX, or TXT."}
#     else:
#         return {"error": "Invalid input. Provide either text or a valid file."}

#     # Build prompt
#     prompt = f"""
#     Generate {numOfQuestions} {difficultyLevel} {typeOfQuestions} questions based on this text:

#     {text_source}

#     Provide the response in JSON format, following this structure:

#     [{{
#       "questionNumber": 1,
#       "question": "What is the capital of France?",
#       "options": ["Paris", "London", "Berlin", "Madrid"],
#       "correctAnswer": "Paris",
#       "explanation": "Paris is the capital of France."
#     }}]
#     Only return valid JSON without extra explanation or Markdown.
#     """

#     try:
#         response = model.generate_content([prompt])
#         response_text = response.text

#         # Handle extra formatting issues
#         cleaned_response = response_text.strip().strip("```json").strip("```")
#         parsed_data = json.loads(cleaned_response)

#         return {"questionData": [McqQuestion(**q) for q in parsed_data]}

#     except json.JSONDecodeError:
#         return {"error": "The model did not return valid JSON. Try reducing input size or rephrasing text."}
#     except Exception as e:
#         print("Error:", e)
#         return {"error": f"Gemini API failed: {str(e)}"}

# # Run the app
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)

import os
import json
import fitz  # PyMuPDF for PDF text extraction
import docx  # python-docx for DOCX extraction
from pptx import Presentation
from pathlib import Path
from typing import List, Optional, Union

from fastapi import FastAPI, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
import uvicorn

# Load .env file
load_dotenv()
load_dotenv()
API_KEY = os.getenv("gemniKey")

if not API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in .env")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")
model = genai.GenerativeModel("gemini-1.5-flash") 

UPLOAD_DIR = Path("Uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class McqQuestion(BaseModel):
    questionNumber: int
    question: str
    options: List[str]
    correctAnswer: str
    explanation: str

def extract_text_from_file(file_path: str) -> str:
    ext = file_path.split('.')[-1].lower()
    try:
        if ext == "pdf":
            doc = fitz.open(file_path)
            return "\n".join(page.get_text("text") for page in doc)
        elif ext == "docx":
            doc = docx.Document(file_path)
            return "\n".join(para.text for para in doc.paragraphs)
        elif ext == "txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        elif ext == "pptx":
            prs = Presentation(file_path)
            text_runs = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text_runs.append(shape.text)
            text = "\n".join(text_runs)
            return text
        else:
            return ""
    except Exception as e:
        print("Error reading file:", e)
        return ""

@app.post("/generateQuestions")
async def generate_questions(
    sourceType: str = Form(...),
    textInput: Optional[str] = Form(None),
    numOfQuestions: int = Form(...),
    difficultyLevel: str = Form(...),
    typeOfQuestions: str = Form(...),
    language: str = Form("English"),  # ✅ new option for language
    fileInput: Optional[UploadFile] = File(None)
) -> Union[List[McqQuestion], dict]:

    if sourceType == "TEXT":
        text_source = textInput
    elif sourceType == "FILE" and fileInput:
        save_to = UPLOAD_DIR / fileInput.filename
        with open(save_to, 'wb') as f:
            f.write(await fileInput.read())
        text_source = extract_text_from_file(str(save_to))
        os.remove(save_to)
        if not text_source.strip():
            return {"error": "Could not extract text from the file. Ensure it's a readable PDF, DOCX, or TXT."}
    else:
        return {"error": "Invalid input. Provide either text or a valid file."}

    prompt = f"""
    Generate {numOfQuestions} {difficultyLevel} {typeOfQuestions} questions in {language} based on this text:

    {text_source}

    Provide the response in JSON format, following this structure:

    [{{
      "questionNumber": 1,
      "question": "What is the capital of France?",
      "options": ["Paris", "London", "Berlin", "Madrid"],
      "correctAnswer": "Paris",
      "explanation": "Paris is the capital of France."
    }}]

    Only return valid JSON without explanation or Markdown.
    If the selected language is Arabic, translate everything (questions, answers, explanation) properly.
    Please follow this schema in your response:
        questionNumber: integer
        question: string
        options: List[string]
        correctAnswer: string
        explanation: string
    In true and false question provide the options as "options": ["True","False"]
    Only return valid JSON without extra explanation or Markdown.
    
    """

    try:
        response = model.generate_content([prompt])
        response_text = response.text

        cleaned_response = response_text.strip().strip("```json").strip("```")
        parsed_data = json.loads(cleaned_response)

        return {"questionData": [McqQuestion(**q) for q in parsed_data]}

    except json.JSONDecodeError:
        return {"error": "The model did not return valid JSON. Try reducing input size or rephrasing text."}
    except Exception as e:
        print("Error:", e)
        return {"error": f"Gemini API failed: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
