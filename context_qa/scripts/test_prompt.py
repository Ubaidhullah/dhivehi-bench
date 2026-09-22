import json
import random
import os
import sys
from google import genai

GEMINI_API_KEY = "AQ.Ab8RN6IYCuYrtd8rRDmoEiaTcoys8kvZShxFCCE70SBdFRn2MQ"
client = genai.Client(api_key=GEMINI_API_KEY)

def test_new_prompt():
    input_file = "context_qa/data/context_qa_dataset_curated.jsonl"
    
    contexts_by_cat = {}
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            cat = data.get("category", "Unknown")
            if cat not in contexts_by_cat:
                contexts_by_cat[cat] = set()
            contexts_by_cat[cat].add(data["context"])
            
    samples = []
    categories = list(contexts_by_cat.keys())
    
    for cat in categories:
        if contexts_by_cat[cat]:
            ctx = random.choice(list(contexts_by_cat[cat]))
            samples.append((cat, ctx))
            contexts_by_cat[cat].remove(ctx)
            
    while len(samples) < 10:
        cat = random.choice(categories)
        if contexts_by_cat[cat]:
            ctx = random.choice(list(contexts_by_cat[cat]))
            samples.append((cat, ctx))
            contexts_by_cat[cat].remove(ctx)
            
    samples = samples[:10]
    
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

    results = []
    print(f"Testing new prompt on {len(samples)} samples...", flush=True)
    
    for i, (cat, ctx) in enumerate(samples):
        print(f"Processing sample {i+1}/10 ({cat})...", flush=True)
        prompt = prompt_template.format(text=ctx)
        
        try:
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt
            )
            cleaned_text = response.text.strip()
            results.append({
                "category": cat,
                "original": ctx,
                "cleaned": cleaned_text
            })
            print(f"-> Success", flush=True)
        except Exception as e:
            print(f"-> Error: {e}", flush=True)
            
    artifact_path = "/Users/ubaidhullahhameed/.gemini/antigravity-cli/brain/ba90f708-8b3d-41f1-8317-e820154596cc/prompt_test_results.md"
    with open(artifact_path, "w", encoding="utf-8") as f:
        f.write("# OCR Cleaning Prompt Test (10 Samples)\n\n")
        for i, res in enumerate(results):
            f.write(f"## Sample {i+1} | Category: {res['category']}\n\n")
            f.write("### Original (Corrupted)\n")
            f.write(f"> {res['original']}\n\n")
            f.write("### Cleaned (New Prompt)\n")
            f.write(f"> {res['cleaned']}\n\n")
            f.write("---\n\n")
            
    print(f"Results saved to {artifact_path}", flush=True)

if __name__ == "__main__":
    test_new_prompt()
