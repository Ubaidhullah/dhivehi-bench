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

GEMINI_API_KEY = "AQ.Ab8RN6IYCuYrtd8rRDmoEiaTcoys8kvZShxFCCE70SBdFRn2MQ"
client = genai.Client(api_key=GEMINI_API_KEY)

class QAPair(BaseModel):
    question: str = Field(description="A question in Dhivehi that can be answered strictly using the provided context.")
    answer: str = Field(description="The exact answer or explanation in Dhivehi, derived ONLY from the context.")

class ContextQASet(BaseModel):
    qa_pairs: List[QAPair] = Field(description="List of 2 Question-Answer pairs.")

def generate_qa_for_paragraph(context_text: str) -> ContextQASet:
    model_name = 'gemini-3.6-flash'
    prompt = f"""
    You are an expert academic examiner specializing in the Dhivehi language.
    Your task is to create a reading comprehension (SQuAD-style) dataset.
    
    Given the following Dhivehi paragraph, generate exactly 2 Question-Answer pairs.
    
    CRITICAL RULES:
    1. The 'question' must ask about a specific fact, event, or concept found IN THIS PARAGRAPH.
    2. The 'answer' MUST be strictly based on the paragraph. Do not use outside knowledge.
    3. Both the question and answer must be in clear, academic Dhivehi.
    4. Do not use phrases like "According to the paragraph". Make the question sound natural.
    
    Paragraph:
    {context_text}
    """

    for attempt in range(5):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    response_schema=ContextQASet,
                ),
            )
            return response.parsed
        except APIError as e:
            if "429" in str(e) or "quota" in str(e).lower():
                time.sleep((2 ** attempt) * 2)
            else:
                return None
        except Exception as e:
            return None
    return None

def split_into_paragraphs(text: str, min_chars=300, max_chars=1200) -> List[str]:
    # Split by double newline to get natural paragraphs
    raw_paras = text.split('\n\n')
    valid_paras = []
    current = ""
    for p in raw_paras:
        p = p.strip()
        if not p: continue
        if len(current) + len(p) < max_chars:
            current += p + "\n\n"
        else:
            if len(current) > min_chars:
                valid_paras.append(current.strip())
            current = p + "\n\n"
    if len(current) > min_chars:
        valid_paras.append(current.strip())
    return valid_paras

file_lock = threading.Lock()

def process_file(filename: str, input_dir: str, output_file: str, pdf_to_category: dict):
    file_path = os.path.join(input_dir, filename)
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    paragraphs = split_into_paragraphs(content)
    
    # Cap to 5 paragraphs per file so we get a diverse set of documents
    paragraphs = paragraphs[:5]
    
    pdf_name = filename.replace(".txt", ".pdf")
    category = pdf_to_category.get(pdf_name, "Unknown")
    
    all_rows = []
    for para in paragraphs:
        result = generate_qa_for_paragraph(para)
        if result and hasattr(result, 'qa_pairs'):
            for qa in result.qa_pairs:
                row = {
                    "source_file": filename,
                    "category": category,
                    "context": para,
                    "question": qa.question,
                    "answer": qa.answer
                }
                all_rows.append(row)
                
    if all_rows:
        with file_lock:
            with open(output_file, "a", encoding="utf-8") as out_f:
                for row in all_rows:
                    out_f.write(json.dumps(row, ensure_ascii=False) + "\n")

def main():
    input_dir = "mcq/data/extracted_text"
    output_file = "context_qa/data/context_qa_dataset.jsonl"
    
    # Pre-compute categories
    pdf_to_category = {}
    for root, dirs, files in os.walk("mcq/data/saruna"):
        for f in files:
            if f.endswith(".pdf"):
                cat = os.path.basename(root)
                pdf_to_category[f] = cat

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
                    
    files_to_process = [f for f in txt_files if f not in processed_files]
    
    print(f"Total files: {len(txt_files)}")
    print(f"Already processed: {len(processed_files)}")
    print(f"Remaining: {len(files_to_process)}")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        list(tqdm(executor.map(lambda f: process_file(f, input_dir, output_file, pdf_to_category), files_to_process), total=len(files_to_process)))

if __name__ == "__main__":
    main()
