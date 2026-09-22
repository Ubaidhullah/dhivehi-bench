import os
import json
import time
from typing import List, Dict
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from google.genai.errors import APIError
from tqdm import tqdm
import concurrent.futures
import threading

GEMINI_API_KEY = "AQ.Ab8RN6IYCuYrtd8rRDmoEiaTcoys8kvZShxFCCE70SBdFRn2MQ"
client = genai.Client(api_key=GEMINI_API_KEY)

class CleanedContext(BaseModel):
    cleaned_text: str = Field(description="The OCR-corrected Dhivehi text.")

def clean_ocr_text(text: str) -> str:
    model_name = 'gemini-3.6-flash'
    prompt = f"""
    You are an expert Dhivehi language editor. 
    The following Dhivehi text was extracted from an old PDF via OCR and contains typographical errors, gibberish, missing spaces, and repeated letters (akuru).
    
    Your task is to fix all OCR and spelling errors to make it readable and grammatically correct Dhivehi.
    
    CRITICAL RULES:
    1. Do NOT paraphrase, summarize, or change the meaning of the text.
    2. Do NOT add new information.
    3. Keep the exact same sentences, just fix the misspelled words and artifacts.
    4. Return ONLY the cleaned Dhivehi text.
    
    Original OCR Text:
    {text}
    """

    for attempt in range(5):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    response_schema=CleanedContext,
                ),
            )
            if response.parsed and hasattr(response.parsed, 'cleaned_text'):
                return response.parsed.cleaned_text
            return text # fallback to original if parsing fails
        except APIError as e:
            if "429" in str(e) or "quota" in str(e).lower():
                time.sleep((2 ** attempt) * 2)
            else:
                return text
        except Exception as e:
            return text
    return text

def main():
    input_file = "context_qa/data/context_qa_dataset_curated.jsonl"
    output_file = "context_qa/data/context_qa_dataset_polished.jsonl"
    
    # 1. Load dataset
    dataset = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            dataset.append(json.loads(line))
            
    # 2. Extract unique contexts
    unique_contexts = list(set([row["context"] for row in dataset]))
    print(f"Total QA Pairs: {len(dataset)}")
    print(f"Unique Contexts to Clean: {len(unique_contexts)}")
    
    # 3. Clean contexts in parallel
    cleaned_map = {}
    lock = threading.Lock()
    
    def process_context(ctx):
        cleaned = clean_ocr_text(ctx)
        with lock:
            cleaned_map[ctx] = cleaned
            
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        list(tqdm(executor.map(process_context, unique_contexts), total=len(unique_contexts)))
        
    # 4. Map cleaned contexts back to the dataset
    print("Mapping cleaned contexts back to the dataset...")
    for row in dataset:
        original_ctx = row["context"]
        row["context"] = cleaned_map.get(original_ctx, original_ctx)
        
    # 5. Save the final polished dataset
    with open(output_file, "w", encoding="utf-8") as f:
        for row in dataset:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            
    print("Done! Polished dataset saved.")

if __name__ == "__main__":
    main()
