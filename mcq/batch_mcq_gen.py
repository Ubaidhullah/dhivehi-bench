import os
import json
import time
from typing import List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv
from tqdm import tqdm

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

def generate_mcqs(text: str, num_questions: int = 5) -> MCQSet:
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

def main():
    input_dir = "mcq/data/extracted_text"
    output_file = "mcq/data/mcq_dataset.jsonl"
    
    # Get all txt files
    txt_files = [f for f in os.listdir(input_dir) if f.endswith(".txt")]
    print(f"Found {len(txt_files)} text files to process.")
    
    with open(output_file, "a", encoding="utf-8") as out_f:
        for filename in tqdm(txt_files):
            file_path = os.path.join(input_dir, filename)
            
            with open(file_path, "r", encoding="utf-8") as f:
                # We'll read the first 4000 characters to ensure we give it enough context 
                # but don't overwhelm the context window unnecessarily for 5 questions
                content = f.read()[:4000]
                
            if len(content.strip()) < 200:
                continue # Skip files that are too short
                
            result = generate_mcqs(content, num_questions=5)
            
            if result and hasattr(result, 'mcqs'):
                for mcq in result.mcqs:
                    # Construct a json line with metadata
                    row = {
                        "source_file": filename,
                        "question": mcq.question,
                        "options": mcq.options,
                        "answer": mcq.answer,
                        "explanation": mcq.explanation
                    }
                    out_f.write(json.dumps(row, ensure_ascii=False) + "\n")
            
            # Sleep briefly to avoid hitting rate limits too quickly
            time.sleep(2)

if __name__ == "__main__":
    main()
