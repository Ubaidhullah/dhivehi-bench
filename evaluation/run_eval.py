#!/usr/bin/env python3
"""
Dhivehi-Bench Master Evaluation Runner
======================================
Executes baseline evaluations for frontier open-weights models (Gemma 4 31B,
Llama 3.1 70B, Qwen 2.5 72B) across the three Dhivehi-Bench tracks:
  1. Multiple Choice Questions (MCQ) - Length-normalized log-likelihood / options
  2. Contextual Question Answering (SQuAD-style)
  3. Bidirectional Translation (EN->DV and DV->EN)

Usage:
  export OPENROUTER_API_KEY="your-api-key"
  python evaluation/run_eval.py --model gemma4 --task all
  python evaluation/run_eval.py --model llama70b --task mcq
  python evaluation/run_eval.py --model qwen72b --task squad
"""

import argparse
import asyncio
import json
import os
import re
import sys
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm

MODEL_MAP = {
    "gemma4": "google/gemma-4-31b-it",
    "llama70b": "meta-llama/llama-3.1-70b-instruct",
    "qwen72b": "qwen/qwen-2.5-72b-instruct"
}

def get_client():
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: Please set OPENROUTER_API_KEY or OPENAI_API_KEY in your environment.", file=sys.stderr)
        sys.exit(1)
    base_url = os.environ.get("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    return AsyncOpenAI(api_key=api_key, base_url=base_url)

async def process_item(client, model_id, item, task_type, sem, pbar):
    async with sem:
        if task_type == "squad":
            sys_msg = "You are a direct, concise AI. Read the Dhivehi context and answer the question in Dhivehi. Extract the exact phrasing from the context if possible. Output ONLY the Dhivehi answer."
            user_msg = f"Context:\n{item['context']}\n\nQuestion: {item['question']}\n\nAnswer:"
            max_toks = 1024
        elif task_type == "mcq":
            opts = "\n".join(item["options"]) if isinstance(item["options"], list) else str(item["options"])
            sys_msg = "You are a direct, concise AI. Output ONLY the single letter of the correct answer (A, B, C, or D). Do not output any other text or punctuation."
            user_msg = f"Question: {item['question']}\n\nOptions:\n{opts}\n\nAnswer:"
            max_toks = 8192
        elif task_type == "translation":
            sys_msg = "You are a direct, concise AI. Output ONLY the exact translation in Dhivehi. Do not output English. Do not explain your reasoning. No preamble."
            user_msg = f"Translate the following English text to Dhivehi. Output ONLY the Dhivehi text.\n\nText: {item.get('english', item.get('source', ''))}"
            max_toks = 2048
        elif task_type == "translation_reverse":
            sys_msg = "You are a direct, concise AI. Output ONLY the exact translation in English. Do not output Dhivehi. Do not explain your reasoning. No preamble."
            user_msg = f"Translate the following Dhivehi text to English. Output ONLY the English text.\n\nText: {item.get('dhivehi', item.get('target', ''))}"
            max_toks = 1024
        else:
            raise ValueError(f"Unknown task: {task_type}")

        messages = [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": user_msg}
        ]

        try:
            response = await client.chat.completions.create(
                model=model_id,
                messages=messages,
                max_tokens=max_toks,
                temperature=0.0
            )
            pred = response.choices[0].message.content
            if pred is None:
                pred = "ERROR: None"
            else:
                pred = pred.strip()
                if task_type == "mcq" and len(pred) > 0:
                    match = re.search(r'[A-D]', pred.upper())
                    pred = match.group(0) if match else pred[0].upper()
        except Exception as e:
            pred = f"ERROR: {str(e)}"

        pbar.update(1)

        result = dict(item)
        result["prediction"] = pred
        return result

async def run_task(client, model_id, model_name, task_type, data_path, out_dir="results", concurrency=10):
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f"{task_type}_{model_name}_eval.json")
    
    print(f"\n--- Running Task: {task_type.upper()} on {model_id} ---")
    print(f"Data source: {data_path}")
    
    items = []
    if data_path.endswith(".jsonl"):
        with open(data_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    items.append(json.loads(line))
    else:
        with open(data_path, "r", encoding="utf-8") as f:
            items = json.load(f)
            
    print(f"Loaded {len(items)} items. Concurrency: {concurrency}")
    sem = asyncio.Semaphore(concurrency)
    pbar = tqdm(total=len(items), desc=f"{model_name}-{task_type}")

    tasks = [process_item(client, model_id, item, task_type, sem, pbar) for item in items]
    results = await asyncio.gather(*tasks)
    pbar.close()

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(results)} outputs to {out_file}")

def main():
    parser = argparse.ArgumentParser(description="Dhivehi-Bench Baseline Evaluation Runner")
    parser.add_argument("--model", type=str, default="gemma4", choices=list(MODEL_MAP.keys()), help="Model family to evaluate")
    parser.add_argument("--task", type=str, default="all", choices=["mcq", "squad", "translation", "translation_reverse", "all"])
    parser.add_argument("--concurrency", type=int, default=10, help="Number of concurrent requests")
    parser.add_argument("--out_dir", type=str, default="results")
    args = parser.parse_args()

    client = get_client()
    model_id = MODEL_MAP[args.model]

    tasks_to_run = ["mcq", "squad", "translation"] if args.task == "all" else [args.task]
    paths = {
        "mcq": "mcq/data/mcq_dataset_categorized.jsonl",
        "squad": "context_qa/data/dhivehi_squad.jsonl",
        "translation": "translation/translation.jsonl",
        "translation_reverse": "translation/translation.jsonl"
    }

    for t in tasks_to_run:
        p = paths[t]
        if not os.path.exists(p):
            print(f"Warning: Data file {p} not found. Skipping {t}.")
            continue
        asyncio.run(run_task(client, model_id, args.model, t, p, out_dir=args.out_dir, concurrency=args.concurrency))

if __name__ == "__main__":
    main()
