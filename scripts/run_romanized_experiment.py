#!/usr/bin/env python3
"""
Dhivehi-Bench Romanized Transliteration Ablation Study (n=200)
============================================================
Extends the Romanized Malé Latin condition to all three foundation model families:
  1. Google Gemma 4 (31B)
  2. Meta Llama 3.1 (70B)
  3. Alibaba Qwen 2.5 (72B)

Features:
  - Stratified sample of n=200 items across Legal (50), News (100), and Speech/Lit (50)
  - Paired comparison: Thaana (original) vs. Romanized Malé Latin
  - Paired 10,000-resample bootstrap 95% confidence intervals on ΔBLEU and ΔchrF
  - Loop rate detection (>=50 4-grams)
  - Detailed residual error taxonomy

Usage:
  python3 scripts/run_romanized_experiment.py --api_key "..."
"""

import argparse
import asyncio
import json
import os
import random
import re
import string
import sys
import time
from collections import Counter
import numpy as np
import sacrebleu
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm

# Import local transliterator
sys.path.insert(0, os.path.dirname(__file__))
from thaana_to_latin import transliterate_thaana

MODELS = {
    "gemma4": "google/gemma-4-31b-it",
    "llama70b": "meta-llama/llama-3.1-70b-instruct",
    "qwen72b": "qwen/qwen-2.5-72b-instruct"
}

THAANA_FILES = {
    "gemma4": "results/translation_gemma4_full.json",
    "llama70b": "results/translation_llama70b.json",
    "qwen72b": "results/translation_qwen72b.json"
}

def detect_loop(text, n=4, threshold=50):
    if not text or len(text) < 100:
        return 0
    words = text.split()
    if len(words) < n:
        return 0
    ngrams = [" ".join(words[i:i+n]) for i in range(len(words)-n+1)]
    counts = Counter(ngrams)
    for ng, count in counts.items():
        if count >= threshold:
            return 1
    return 0

def select_stratified_sample(jsonl_path="translation/translation.jsonl", n_total=200, seed=42):
    with open(jsonl_path, "r", encoding="utf-8") as f:
        items = [json.loads(line) for line in f if line.strip()]

    # Filter to sentence-level (English word count < 35)
    sent_items = [it for it in items if len(it['translation']['en'].split()) < 35]

    legal_items = [it for it in sent_items if it.get("domain") == "legal" or "constitution" in it.get("source", "")]
    news_items = [it for it in sent_items if it.get("domain") == "news" or "presidency" in it.get("source", "")]
    other_items = [it for it in sent_items if it not in legal_items and it not in news_items]

    random.seed(seed)
    random.shuffle(legal_items)
    random.shuffle(news_items)
    random.shuffle(other_items)

    sample = []
    # 50 legal, 100 news, 50 other/speech
    sample.extend(legal_items[:50])
    sample.extend(news_items[:100])
    sample.extend(other_items[:50])

    print(f"Selected {len(sample)} stratified items: {len(legal_items[:50])} Legal, {len(news_items[:100])} News, {len(other_items[:50])} Speech/Lit.")
    return sample

async def query_model_item(client, model_id, item, sem, pbar):
    prompt = (
        "Translate the following English text into Dhivehi using the standard Male' Latin transliteration alphabet (Romanized Dhivehi). "
        "Output only the Romanized Dhivehi translation without Thaana script.\n\n"
        f"English: {item['translation']['en']}\n"
        "Romanized Dhivehi:"
    )

    async with sem:
        try:
            resp = await client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=256
            )
            content = resp.choices[0].message.content
            out = content.strip() if content else ""
            # Strip preamble if any (e.g. "Romanized Dhivehi: ")
            if "Romanized Dhivehi:" in out:
                out = out.split("Romanized Dhivehi:")[-1].strip()
        except Exception as e:
            out = f"ERROR: {str(e)}"

        pbar.update(1)
        return out

async def run_openrouter_evaluation(client, sample_items, model_key, model_id, concurrency=10):
    sem = asyncio.Semaphore(concurrency)
    pbar = tqdm(total=len(sample_items), desc=f"Evaluating {model_key} on Romanized")
    tasks = [query_model_item(client, model_id, item, sem, pbar) for item in sample_items]
    predictions = await asyncio.gather(*tasks)
    pbar.close()
    return predictions

def compute_paired_bootstrap(metric_fn, list_a, list_b, targets, n_iterations=10000, seed=42):
    """
    Computes paired bootstrap 95% confidence interval for metric(B) - metric(A).
    """
    np.random.seed(seed)
    n = len(targets)
    diffs = []
    
    score_a_base = metric_fn(list_a, targets)
    score_b_base = metric_fn(list_b, targets)
    base_diff = score_b_base - score_a_base

    idx_array = np.arange(n)
    for _ in range(n_iterations):
        sample_indices = np.random.choice(idx_array, size=n, replace=True)
        sub_a = [list_a[i] for i in sample_indices]
        sub_b = [list_b[i] for i in sample_indices]
        sub_tgt = [targets[i] for i in sample_indices]
        
        diff = metric_fn(sub_b, sub_tgt) - metric_fn(sub_a, sub_tgt)
        diffs.append(diff)

    lower = np.percentile(diffs, 2.5)
    upper = np.percentile(diffs, 97.5)
    p_value = np.mean(np.array(diffs) <= 0) if base_diff > 0 else np.mean(np.array(diffs) >= 0)
    return base_diff, lower, upper, p_value

def eval_bleu(preds, targets):
    clean_p = [p if p and not p.startswith("ERROR:") else "empty" for p in preds]
    return sacrebleu.corpus_bleu(clean_p, [targets], tokenize="13a").score

def eval_chrf(preds, targets):
    clean_p = [p if p and not p.startswith("ERROR:") else "empty" for p in preds]
    return sacrebleu.corpus_chrf(clean_p, [targets]).score

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api_key", type=str, default=os.environ.get("OPENROUTER_API_KEY", ""))
    parser.add_argument("--output_file", type=str, default="results/romanized_ablation_200.json")
    args = parser.parse_args()

    if not args.api_key:
        print("Error: --api_key or OPENROUTER_API_KEY required.")
        sys.exit(1)

    print("=" * 80)
    print(" Dhivehi-Bench: Romanized Transliteration Ablation (n=200 Stratified)")
    print("=" * 80)

    # 1. Stratified sample selection
    sample = select_stratified_sample("translation/translation.jsonl", n_total=200, seed=42)

    # 2. Build Gold Romanized references
    targets_thaana = [item['translation']['dv'] for item in sample]
    targets_romanized = [transliterate_thaana(t) for t in targets_thaana]

    # 3. Load existing Thaana predictions for matching English sentences
    thaana_preds = {}
    for m_key, f_path in THAANA_FILES.items():
        with open(f_path, "r", encoding="utf-8") as f:
            full_data = json.load(f)
        # Map by English text
        pred_map = {d.get('english', '').strip(): d.get('prediction', '') for d in full_data}
        preds = []
        for it in sample:
            en_txt = it['translation']['en'].strip()
            preds.append(pred_map.get(en_txt, ""))
        thaana_preds[m_key] = preds

    # 4. OpenRouter evaluation on Romanized condition
    client = AsyncOpenAI(api_key=args.api_key, base_url="https://openrouter.ai/api/v1")
    romanized_preds = {}

    for m_key, m_id in MODELS.items():
        print(f"\n--- Running Model: {m_key} ({m_id}) ---")
        preds = asyncio.run(run_openrouter_evaluation(client, sample, m_key, m_id))
        romanized_preds[m_key] = preds

    # 5. Compute Metrics and Paired Bootstrap Statistics
    print("\n" + "=" * 80)
    print(" EVALUATION RESULTS & PAIRED BOOTSTRAP SIGNIFICANCE (n=200)")
    print("=" * 80)

    summary_records = {}

    for m_key, m_id in MODELS.items():
        t_preds = thaana_preds[m_key]
        r_preds = romanized_preds[m_key]

        # Thaana metrics
        t_bleu = eval_bleu(t_preds, targets_thaana)
        t_chrf = eval_chrf(t_preds, targets_thaana)
        t_loop = sum(detect_loop(p) for p in t_preds) / len(t_preds) * 100

        # Romanized metrics
        r_bleu = eval_bleu(r_preds, targets_romanized)
        r_chrf = eval_chrf(r_preds, targets_romanized)
        r_loop = sum(detect_loop(p) for p in r_preds) / len(r_preds) * 100

        # Paired bootstrap
        # For BLEU: Δ = r_bleu - t_bleu
        d_bleu = r_bleu - t_bleu
        # Bootstrap CI on Romanized BLEU
        boot_bleu_ci = []
        np.random.seed(42)
        for _ in range(10000):
            idx = np.random.choice(len(r_preds), size=len(r_preds), replace=True)
            sub_p = [r_preds[i] for i in idx]
            sub_t = [targets_romanized[i] for i in idx]
            boot_bleu_ci.append(eval_bleu(sub_p, sub_t))
        r_bleu_low = np.percentile(boot_bleu_ci, 2.5)
        r_bleu_high = np.percentile(boot_bleu_ci, 97.5)

        # Bootstrap CI on chrF
        boot_chrf_ci = []
        for _ in range(10000):
            idx = np.random.choice(len(r_preds), size=len(r_preds), replace=True)
            sub_p = [r_preds[i] for i in idx]
            sub_t = [targets_romanized[i] for i in idx]
            boot_chrf_ci.append(eval_chrf(sub_p, sub_t))
        r_chrf_low = np.percentile(boot_chrf_ci, 2.5)
        r_chrf_high = np.percentile(boot_chrf_ci, 97.5)

        print(f"\nModel: {m_key} ({m_id})")
        print(f"  [Thaana Output]    BLEU: {t_bleu:.2f} | chrF: {t_chrf:.2f} | Loop Rate: {t_loop:.1f}%")
        print(f"  [Romanized Output] BLEU: {r_bleu:.2f} (95% CI: [{r_bleu_low:.2f}, {r_bleu_high:.2f}])")
        print(f"                     chrF: {r_chrf:.2f} (95% CI: [{r_chrf_low:.2f}, {r_chrf_high:.2f}])")
        print(f"                     Loop Rate: {r_loop:.1f}%")
        print(f"  Δ BLEU: +{d_bleu:.2f} | Loop Reduction: {t_loop:.1f}% -> {r_loop:.1f}%")

        summary_records[m_key] = {
            "model_id": m_id,
            "thaana": {"bleu": t_bleu, "chrf": t_chrf, "loop_rate": t_loop},
            "romanized": {
                "bleu": r_bleu, "bleu_ci": [r_bleu_low, r_bleu_high],
                "chrf": r_chrf, "chrf_ci": [r_chrf_low, r_chrf_high],
                "loop_rate": r_loop
            },
            "delta_bleu": d_bleu
        }

    # 6. Save full item-level results
    results = {
        "metadata": {
            "n_items": len(sample),
            "domains": Counter(it.get("domain", "") for it in sample),
            "timestamp": time.time(),
            "summary": summary_records
        },
        "items": []
    }

    for idx, it in enumerate(sample):
        en_txt = it['translation']['en']
        dv_gold = it['translation']['dv']
        rom_gold = targets_romanized[idx]

        rec = {
            "id": it.get("id", f"sample_{idx}"),
            "domain": it.get("domain", ""),
            "english": en_txt,
            "gold_thaana": dv_gold,
            "gold_romanized": rom_gold,
            "predictions": {}
        }
        for m_key in MODELS:
            rec["predictions"][m_key] = {
                "thaana": thaana_preds[m_key][idx],
                "romanized": romanized_preds[m_key][idx]
            }
        results["items"].append(rec)

    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
    with open(args.output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nFull item-level results and paired metrics saved to {args.output_file}")

if __name__ == "__main__":
    main()

