import google.generativeai as genai
import typing_extensions as typing
from fastapi import FastAPI, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Union
import uvicorn
import os
import json
from pathlib import Path
import fitz  # PyMuPDF for PDF text extraction
import docx  # python-docx for DOCX extraction

UPLOAD_DIR = Path() / 'Uploads'
UPLOAD_DIR.mkdir(exist_ok=True)  # Ensure upload directory exists

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

class McqQuestion(BaseModel):
    questionNumber: int
    question: str
    options: List[str]
    correctAnswer: str
    explanation: str


def extract_text_from_file(file_path: str) -> str:
    """Extract text from PDF, DOCX, and TXT files."""
    ext = file_path.split('.')[-1].lower()
    if ext == "pdf":
        doc = fitz.open(file_path)
        text = "\n".join(page.get_text("text") for page in doc)
    elif ext == "docx":
        doc = docx.Document(file_path)
        text = "\n".join(para.text for para in doc.paragraphs)
    elif ext == "txt":
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = ""
    return text

@app.post("/generateQuestions")
async def generate_questions(
    sourceType: str = Form(...),
    textInput: Optional[str] = Form(None),
    numOfQuestions: int = Form(...),
    difficultyLevel: str = Form(...),
    typeOfQuestions: str = Form(...),
    fileInput: Optional[UploadFile] = File(None)
) -> Union[List[McqQuestion], dict]:
    
    API_KEY = os.getenv("gemniKey")
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-pro')

    if sourceType == "TEXT":
        text_source = textInput
    elif sourceType == "FILE" and fileInput:
        save_to = UPLOAD_DIR / fileInput.filename ## ToDo: add random number or dateNow in seconds to the file name
        with open(save_to, 'wb') as f:
            f.write(await fileInput.read())

        text_source = extract_text_from_file(str(save_to))
        if not text_source.strip():
            return {"error": "Could not extract text from the file. Ensure it's a readable PDF, DOCX, or TXT."}
    else:
        return {"error": "Invalid input. Provide either text or a valid file."}

    # Define the structured prompt
    prompt = f"""
    Generate {numOfQuestions} {difficultyLevel} {typeOfQuestions} questions based on this text:
    
    {text_source}
    
    Provide the response in JSON format, following this structure:
    
    - If MCQ:
    [{{
      "questionNumber": 1,
      "question": "What is the capital of France?",
      "options": ["Paris", "London", "Berlin", "Madrid"],
      "correctAnswer": "Paris",
      "explanation": "Paris is the capital of France."
    }}]
    
    - If True/False:
    [{{
      "questionNumber": 1,
      "question": "The sun rises in the west.",
      "options": ["True", "False"],
      "correctAnswer": "False",
      "explanation": "The sun rises in the east."
    }}]

    please don't add any new lines
    """

    response = model.generate_content([prompt])
    print(response.text)
    try:
        parsed_data = json.loads(response.text)
        responseQuestions = {"questionData": [McqQuestion(**q) for q in parsed_data]}
        print(responseQuestions)
        return responseQuestions

    except json.JSONDecodeError:
        return {"error": "Failed to parse AI response. Ensure the API is returning valid JSON."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

