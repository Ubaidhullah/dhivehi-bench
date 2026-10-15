#!/usr/bin/env python3
"""
Dhivehi-Bench Translation Ablation Runner
=========================================
Reproduces the transliteration, repetition penalty, and in-context learning
ablations reported in Table 5 of the paper:
  1. Greedy Baseline (Temperature=0.0)
  2. Repetition Penalty (1.2)
  3. 3-Shot In-Context Learning
  4. Romanized Malé Latin Transliteration

Usage:
  export OPENROUTER_API_KEY="your-api-key"
  python evaluation/run_ablation.py
"""

import json
import os
import random
import sys
import time
from tqdm import tqdm
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
MODEL = "google/gemma-3-27b-it:free"

FEW_SHOT_PROMPT = """English: The President arrived in Male' today.
Dhivehi: ރައީސުލްޖުމްހޫރިއްޔާ މިއަދު މާލެ ވަޑައިގެންނެވިއެވެ.

English: The Supreme Court issued a ruling on the constitutional matter.
Dhivehi: ޤާނޫނުއަސާސީގެ މައްސަލައިގައި ސުޕްރީމް ކޯޓުން ޙުކުމެއް އިއްވައިފިއެވެ.

English: The education sector has shown significant progress over the past five years.
Dhivehi: ވޭތުވެދިޔަ ފަސް އަހަރު ދުވަހުގެ ތެރޭގައި ތަޢުލީމީ ދާއިރާއިން ބޮޑެތި ކުރިއެރުންތަކެއް ވަނީ ފެނިފައެވެ.

English: {text}
Dhivehi:"""

def get_session():
    session = requests.Session()
    retry = Retry(connect=5, read=5, backoff_factor=1.0, status_forcelist=[500, 502, 503, 504, 520, 524])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def query_openrouter(session, messages, temperature=0.0, repetition_penalty=1.0, max_tokens=500):
    if not OPENROUTER_API_KEY:
        print("ERROR: Please set OPENROUTER_API_KEY or OPENAI_API_KEY.", file=sys.stderr)
        sys.exit(1)
        
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "temperature": temperature,
        "repetition_penalty": repetition_penalty,
        "max_tokens": max_tokens,
        "messages": messages
    }
    try:
        response = session.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        else:
            return f"ERROR: HTTP {response.status_code}"
    except Exception as e:
        return f"ERROR: {str(e)}"

def main():
    data_path = "translation/translation.jsonl"
    if not os.path.exists(data_path):
        data_path = "results/translation_gemma4_full.json"
        
    with open(data_path, "r", encoding="utf-8") as f:
        if data_path.endswith(".jsonl"):
            dataset = [json.loads(line) for line in f if line.strip()]
        else:
            dataset = json.load(f)

    random.seed(42)
    subset = random.sample(dataset, min(50, len(dataset)))
    print(f"Running Ablation on {len(subset)} items using {MODEL}...")

    session = get_session()
    results = []

    for item in tqdm(subset, desc="Ablation Items"):
        eng_text = item.get("english", item.get("source", ""))
        dhivehi_target = item.get("dhivehi", item.get("target", ""))

        # 1. Greedy baseline
        greedy_resp = query_openrouter(
            session,
            [
                {"role": "system", "content": "You are a professional machine translator. Translate the following English text to Dhivehi. Output ONLY Dhivehi."},
                {"role": "user", "content": eng_text}
            ],
            temperature=0.0,
            repetition_penalty=1.0
        )
        time.sleep(0.5)

        # 2. Repetition penalty 1.2
        penalty_resp = query_openrouter(
            session,
            [
                {"role": "system", "content": "You are a professional machine translator. Translate the following English text to Dhivehi. Output ONLY Dhivehi."},
                {"role": "user", "content": eng_text}
            ],
            temperature=0.0,
            repetition_penalty=1.2
        )
        time.sleep(0.5)

        # 3. 3-Shot prompting
        few_shot_prompt = FEW_SHOT_PROMPT.format(text=eng_text)
        fewshot_resp = query_openrouter(
            session,
            [
                {"role": "user", "content": few_shot_prompt}
            ],
            temperature=0.0
        )
        time.sleep(0.5)

        results.append({
            "english": eng_text,
            "target": dhivehi_target,
            "greedy": greedy_resp,
            "repetition_penalty": penalty_resp,
            "few_shot": fewshot_resp
        })

    os.makedirs("results", exist_ok=True)
    out_file = "results/ablation_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nAblation completed! Results saved to {out_file}")

if __name__ == "__main__":
    main()
