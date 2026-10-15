#!/usr/bin/env python3
"""
Dhivehi-Bench Unified Scoring Script
====================================
Computes standardized evaluation metrics across all Dhivehi-Bench tracks:
  1. Multiple Choice Questions: Accuracy (%)
  2. Contextual QA (SQuAD): Exact Match (EM %) and Token-level F1 (%)
  3. Translation: BLEU (char-tokenized), chrF, and Loop Rate (>=50 repeat 4-grams)

Usage:
  python evaluation/score_bench.py
  python evaluation/score_bench.py --results_dir results
"""

import argparse
import glob
import json
import os
import re
import string
from collections import Counter
import sacrebleu

def normalize_dhivehi(s):
    if not s:
        return ""
    # Strip Latin punctuation while preserving Thaana fili diacritics
    s = s.lower().strip()
    return ''.join(ch for ch in s if ch not in string.punctuation).strip()

def compute_exact_match(prediction, ground_truth):
    return int(normalize_dhivehi(prediction) == normalize_dhivehi(ground_truth))

def compute_f1(prediction, ground_truth):
    pred_toks = normalize_dhivehi(prediction).split()
    gold_toks = normalize_dhivehi(ground_truth).split()
    common = Counter(pred_toks) & Counter(gold_toks)
    num_same = sum(common.values())
    if num_same == 0:
        return 0.0
    precision = 1.0 * num_same / len(pred_toks)
    recall = 1.0 * num_same / len(gold_toks)
    return (2 * precision * recall) / (precision + recall)

def detect_loop_rate(text, n=4, threshold=50):
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

def score_mcq(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    valid, correct = 0, 0
    for item in data:
        pred = str(item.get("prediction", "")).strip().upper()
        target = str(item.get("target", item.get("answer", ""))).strip().upper()
        if pred.startswith("ERROR:") or not pred:
            continue
        valid += 1
        # Extract first letter A-D
        match = re.search(r'[A-D]', pred)
        p_letter = match.group(0) if match else pred[0]
        if p_letter == target:
            correct += 1
    return {"accuracy": (correct / valid * 100) if valid > 0 else 0.0, "total": valid}

def score_squad(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    em_total, f1_total, valid = 0, 0, 0
    for item in data:
        pred = item.get("prediction", "")
        target = item.get("target", item.get("answer", ""))
        if pred.startswith("ERROR:") or not pred:
            continue
        em_total += compute_exact_match(pred, target)
        f1_total += compute_f1(pred, target)
        valid += 1
    return {
        "exact_match": (em_total / valid * 100) if valid > 0 else 0.0,
        "f1": (f1_total / valid * 100) if valid > 0 else 0.0,
        "total": valid
    }

def score_translation(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    preds, targets = [], []
    loops = 0
    valid = 0
    for item in data:
        pred = item.get("prediction", "").strip()
        target = item.get("target", item.get("dhivehi", "")).strip()
        if pred.startswith("ERROR:") or not pred:
            continue
        valid += 1
        preds.append(pred)
        targets.append(target)
        if detect_loop_rate(pred):
            loops += 1

    if not preds:
        return {"bleu": 0.0, "chrf": 0.0, "loop_rate": 0.0, "total": 0}

    # Standard character-tokenized BLEU and chrF
    bleu = sacrebleu.corpus_bleu(preds, [targets], tokenize="char")
    chrf = sacrebleu.corpus_chrf(preds, [targets])
    loop_rate = (loops / valid * 100) if valid > 0 else 0.0

    return {
        "bleu": bleu.score,
        "chrf": chrf.score,
        "loop_rate": loop_rate,
        "total": valid
    }

def main():
    parser = argparse.ArgumentParser(description="Score Dhivehi-Bench Results")
    parser.add_argument("--results_dir", type=str, default="results")
    args = parser.parse_args()

    print("=" * 75)
    print(" 🇲🇻 Dhivehi-Bench: Benchmark Results Summary")
    print("=" * 75)

    models = [
        ("Gemma 4 (31B)", "gemma4_full"),
        ("Llama 3.1 (70B)", "llama70b"),
        ("Qwen 2.5 (72B)", "qwen72b")
    ]

    print(f"{'Model':<18} | {'MCQ Acc':<9} | {'QA F1':<8} | {'QA EM':<8} | {'EN->DV BLEU':<12} | {'EN->DV chrF'}")
    print("-" * 75)

    for display_name, file_key in models:
        # Check MCQ
        mcq_files = glob.glob(f"{args.results_dir}/mcq*{file_key}*.json") or glob.glob(f"{args.results_dir}/mcq*{file_key.replace('70b','').replace('72b','')}*.json")
        mcq_acc = score_mcq(mcq_files[0])["accuracy"] if mcq_files else None

        # Check QA
        qa_files = glob.glob(f"{args.results_dir}/squad*{file_key}*.json")
        qa_res = score_squad(qa_files[0]) if qa_files else None

        # Check Translation
        trans_files = glob.glob(f"{args.results_dir}/translation*{file_key}*.json")
        trans_res = score_translation(trans_files[0]) if trans_files else None

        acc_str = f"{mcq_acc:.2f}%" if mcq_acc is not None else "--"
        f1_str = f"{qa_res['f1']:.2f}%" if qa_res else "--"
        em_str = f"{qa_res['exact_match']:.2f}%" if qa_res else "--"
        bleu_str = f"{trans_res['bleu']:.2f}" if trans_res else "--"
        chrf_str = f"{trans_res['chrf']:.2f}" if trans_res else "--"

        print(f"{display_name:<18} | {acc_str:<9} | {f1_str:<8} | {em_str:<8} | {bleu_str:<12} | {chrf_str}")

    print("=" * 75)

if __name__ == "__main__":
    main()
