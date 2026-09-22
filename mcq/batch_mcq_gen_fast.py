import os
import json
import time
from typing import List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from google.genai.errors import APIError
from tqdm import tqdm
import concurrent.futures
import threading

# API Client
GEMINI_API_KEY = "AQ.Ab8RN6IYCuYrtd8rRDmoEiaTcoys8kvZShxFCCE70SBdFRn2MQ"
client = genai.Client(api_key=GEMINI_API_KEY)

class MCQ(BaseModel):
    question: str = Field(description="The question text in Dhivehi.")
    options: List[str] = Field(description="Four multiple choice options in Dhivehi. Use format 'A: ...', 'B: ...', etc.")
    answer: str = Field(description="The correct option letter (A, B, C, or D).")
    explanation: str = Field(description="A brief explanation in Dhivehi of why the answer is correct.")

class MCQSet(BaseModel):
    mcqs: List[MCQ] = Field(description="A list of multiple choice questions generated from the text.")

def generate_mcqs_for_chunk(text: str, num_questions: int = 5) -> MCQSet:
    model_name = 'gemini-3.6-flash'
    prompt = f"""
    You are an expert educator and Dhivehi language specialist creating a standalone evaluation benchmark. 
    Your task is to generate {num_questions} high-quality Multiple Choice Questions (MCQs) based on facts found in the provided Dhivehi text.
    
    CRITICAL REQUIREMENTS:
    1. STANDALONE QUESTIONS: The AI models being tested will NOT see the source text. Do NOT use phrases like "ލިޔުމުގައިވާ ގޮތުން" (According to the text), "މި ވާހަކައިގައި" (In this story), or "މަތީގައިވާ" (Above). The question must be a universally understandable general knowledge or factual question that stands entirely on its own.
    2. Each question must be in natural, academic Dhivehi.
    3. Provide 4 options (A, B, C, D) for each question.
    4. Ensure only one option is correct and the distractors are plausible.
    5. Provide a brief explanation for the correct answer.
    
    Text:
    {text}
    """

    max_retries = 5
    for attempt in range(max_retries):
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
        except APIError as e:
            if "429" in str(e) or "quota" in str(e).lower():
                sleep_time = (2 ** attempt) * 2
                time.sleep(sleep_time)
            else:
                print(f"API Error: {e}")
                return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
    return None

def chunk_text(text: str, chunk_size: int = 4000) -> List[str]:
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

file_lock = threading.Lock()

def process_file(filename: str, input_dir: str, output_file: str, category: str):
    file_path = os.path.join(input_dir, filename)
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    if len(content.strip()) < 200:
        return
        
    chunks = chunk_text(content, chunk_size=4000)
    
    all_mcqs = []
    # CAP chunks to 5 per file so we don't blow tokens on massive files in a small category
    max_chunks = 5
    for chunk_idx, chunk in enumerate(chunks[:max_chunks]):
        if len(chunk.strip()) < 200:
            continue
            
        result = generate_mcqs_for_chunk(chunk, num_questions=3) 
        
        if result and hasattr(result, 'mcqs'):
            for mcq in result.mcqs:
                row = {
                    "source_file": filename,
                    "chunk_index": chunk_idx,
                    "question": mcq.question,
                    "options": mcq.options,
                    "answer": mcq.answer,
                    "explanation": mcq.explanation,
                    "category": category,
                    "status": "pending"
                }
                all_mcqs.append(row)
                
    if all_mcqs:
        with file_lock:
            with open(output_file, "a", encoding="utf-8") as out_f:
                for row in all_mcqs:
                    out_f.write(json.dumps(row, ensure_ascii=False) + "\n")

def main():
    input_dir = "mcq/data/extracted_text"
    output_file = "mcq/data/mcq_dataset_categorized.jsonl"
    
    # Pre-compute category mapping
    pdf_to_category = {}
    for root, dirs, files in os.walk("mcq/data/saruna"):
        for f in files:
            if f.endswith(".pdf"):
                # Ensure we strip out the UUID prefix if it exists in the .txt but not .pdf. 
                # Actually, the PDFs in saruna have UUID prefixes already!
                category = os.path.basename(root)
                pdf_to_category[f] = category

    txt_files = [f for f in os.listdir(input_dir) if f.endswith(".txt")]
    
    processed_files = set()
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    processed_files.add(data["source_file"])
                except:
                    pass
                    
    # Categories to skip (overrepresented)
    skip_categories = {"Dhivehi_Language_Studies", "Religion", "Essays"}
    
    files_to_process = []
    for f in txt_files:
        if f in processed_files:
            continue
        # The filename matches exactly except for extension
        pdf_name = f.replace(".txt", ".pdf")
        cat = pdf_to_category.get(pdf_name, "Unknown")
        if cat not in skip_categories:
            files_to_process.append((f, cat))

    print(f"Total extracted files: {len(txt_files)}")
    print(f"Files already processed (all categories): {len(processed_files)}")
    print(f"Remaining targeted files to process (excluding large categories): {len(files_to_process)}")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        list(tqdm(executor.map(lambda item: process_file(item[0], input_dir, output_file, item[1]), files_to_process), total=len(files_to_process)))

if __name__ == "__main__":
    main()
