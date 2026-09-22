import json
import concurrent.futures
from google import genai
import time
import sys

GEMINI_API_KEY = "AQ.Ab8RN6IYCuYrtd8rRDmoEiaTcoys8kvZShxFCCE70SBdFRn2MQ"
client = genai.Client(api_key=GEMINI_API_KEY)

INPUT_FILE = "context_qa/data/context_qa_dataset_filtered.jsonl"
OUTPUT_FILE = "context_qa/data/context_qa_dataset_polished_v2.jsonl"

prompt_template = """You are a native Dhivehi linguistic expert and editor. Your task is to perfectly restore Dhivehi text that was severely corrupted during PDF OCR extraction (often due to complex multi-column layouts and right-to-left reading order).
    
The text has disjointed sentences, incorrect line breaks, repeated letters (akuru), and missing or wrong vowels (fili).

Instructions:
1. Reconstruct the broken sentences so the paragraph flows naturally in standard Dhivehi syntax. Connect sentences that were improperly split by layout errors.
2. Meticulously fix all 'akuru' (letters) and 'fili' (vowels) mistakes caused by OCR. Remove any random gibberish symbols.
3. Ensure the paragraph has a proper ending. If it cuts off abruptly with a meaningless fragmented sentence, safely trim that fragment so the paragraph ends cleanly.
4. Preserve the original meaning and facts entirely. Do not invent new facts.
5. Format the output as a cohesive, beautifully formatted Dhivehi paragraph without unnatural line breaks.

Return ONLY the cleaned Dhivehi text.

Original Corrupted Text:
{text}"""

def clean_paragraph(context):
    prompt = prompt_template.format(text=context)
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Error for context: {e}", flush=True)
        return context  # Fallback to original if API fails completely

def main():
    data = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line))
            
    # Extract unique paragraphs
    unique_contexts = list(set(d['context'] for d in data))
    print(f"Total unique paragraphs to clean: {len(unique_contexts)}", flush=True)
    
    cleaned_mapping = {}
    
    # Process in parallel
    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ctx = {executor.submit(clean_paragraph, ctx): ctx for ctx in unique_contexts}
        for future in concurrent.futures.as_completed(future_to_ctx):
            ctx = future_to_ctx[future]
            cleaned_text = future.result()
            cleaned_mapping[ctx] = cleaned_text
            completed += 1
            if completed % 50 == 0:
                print(f"Progress: {completed}/{len(unique_contexts)}", flush=True)
                
    # Map back to dataset
    for d in data:
        d['context'] = cleaned_mapping.get(d['context'], d['context'])
        d['status'] = 'pending' # Ready for UI manual review
        
    # Save the output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for d in data:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
            
    print(f"Finished! Saved beautifully polished dataset to {OUTPUT_FILE}", flush=True)

if __name__ == "__main__":
    main()
