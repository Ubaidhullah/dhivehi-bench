import json
import concurrent.futures
from google import genai
import time
import os
import shutil

GEMINI_API_KEY = "AQ.Ab8RN6IYCuYrtd8rRDmoEiaTcoys8kvZShxFCCE70SBdFRn2MQ"
client = genai.Client(api_key=GEMINI_API_KEY)

INPUT_FILE = "context_qa/data/context_qa_dataset_polished_v2.jsonl"
OUTPUT_FILE = "context_qa/data/context_qa_dataset_polished_v2.jsonl.tmp"

prompt_template = """You are a native Dhivehi linguistic expert. Review the following Question and Answer pair based on the given Context.
Correct any minor mistakes, spelling errors (akuru/fili), awkward phrasing, or grammatical issues in the Question and Answer.
If the Question asks "According to the text", rephrase it so it is a standalone universal question without mentioning the text.
If they are already perfect, return them exactly as they are.

IMPORTANT: You MUST return valid JSON ONLY, with no markdown formatting, using this exact structure:
{{"question": "...", "answer": "..."}}

Context:
{context}

Original Question:
{question}

Original Answer:
{answer}
"""

def clean_qa(index, row):
    if row.get("status") == "confirmed":
        return index, row
        
    prompt = prompt_template.format(
        context=row["context"],
        question=row["question"],
        answer=row["answer"]
    )
    
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt
        )
        text = response.text.strip()
        
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
            
        result = json.loads(text)
        
        q = result.get("question", row["question"]).strip()
        if q and not q.endswith("؟"):
            q = q[:-1] + "؟" if q.endswith(".") else q + "؟"
            
        a = result.get("answer", row["answer"]).strip()
        
        row["question"] = q
        row["answer"] = a
        return index, row
    except Exception as e:
        print(f"Error at index {index}: {e}", flush=True)
        return index, row

def main():
    data = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line))
            
    total_unconfirmed = sum(1 for d in data if d.get("status") != "confirmed")
    print(f"Total unconfirmed QA pairs to correct: {total_unconfirmed}", flush=True)
    
    results = [None] * len(data)
    completed = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_idx = {executor.submit(clean_qa, i, row): i for i, row in enumerate(data)}
        
        for future in concurrent.futures.as_completed(future_to_idx):
            idx, row = future.result()
            results[idx] = row
            completed += 1
            if completed % 50 == 0:
                print(f"Progress: {completed}/{len(data)}", flush=True)
                
    # Save results
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for row in results:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            
    shutil.move(OUTPUT_FILE, INPUT_FILE)
    print("Finished beautifully! File updated.", flush=True)

if __name__ == "__main__":
    main()
