import os
import json
from typing import List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="translation/dhivehi-english-alignment-engine/.env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

class MCQ(BaseModel):
    question: str = Field(description="The question text in Dhivehi.")
    options: List[str] = Field(description="Four multiple choice options in Dhivehi. Use format 'A: ...', 'B: ...', etc.")
    answer: str = Field(description="The correct option letter (A, B, C, or D).")
    explanation: str = Field(description="A brief explanation in Dhivehi of why the answer is correct.")

class MCQSet(BaseModel):
    mcqs: List[MCQ] = Field(description="A list of multiple choice questions generated from the text.")

def generate_mcqs(text: str, num_questions: int = 3) -> MCQSet:
    model_name = 'gemini-3.6-flash'
    
    prompt = f"""
    You are an expert educator and Dhivehi language specialist. 
    Your task is to generate {num_questions} high-quality Multiple Choice Questions (MCQs) based on the provided Dhivehi text.
    
    Requirements:
    1. Each question must be in natural, academic Dhivehi.
    2. Provide 4 options (A, B, C, D) for each question.
    3. Ensure only one option is correct and the distractors are plausible.
    4. The questions should test understanding of key facts, concepts, or reasoning within the text.
    5. Provide a brief explanation for the correct answer.
    
    Text:
    {text}
    """

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=MCQSet,
            ),
        )
        return response.parsed
    except Exception as e:
        print(f"API Call failed: {e}")
        return None

if __name__ == "__main__":
    # Test with a small sample from extracted text
    sample_file = os.listdir("mcq/data/extracted_text")[0]
    sample_path = os.path.join("mcq/data/extracted_text", sample_file)
    
    with open(sample_path, "r", encoding="utf-8") as f:
        content = f.read()[:2000] # Use first 2000 chars
    
    print(f"Generating MCQs for: {sample_file}")
    result = generate_mcqs(content)
    
    if result:
        print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
    else:
        print("Generation failed.")
