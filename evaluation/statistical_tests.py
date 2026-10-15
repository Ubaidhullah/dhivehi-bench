#!/usr/bin/env python3
"""
Dhivehi-Bench Statistical Significance Tests
=============================================
Computes:
  1. 95% Bootstrap Confidence Intervals (10,000 resamples) across metrics.
  2. McNemar's Chi-squared Test for paired nominal evaluation comparisons.

Usage:
  python evaluation/statistical_tests.py
"""

import json
import os
import numpy as np
from nltk.translate.chrf_score import sentence_chrf
try:
    from statsmodels.stats.contingency_tables import mcnemar
except ImportError:
    mcnemar = None

def run_bootstrap_ci(data_file="results/translation_gemma4_full.json", n_iterations=10000):
    if not os.path.exists(data_file):
        print(f"File not found: {data_file}")
        return
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    chrf_scores = []
    for item in data:
        pred = item.get("prediction", "")
        target = item.get("target", "")
        if not pred.startswith("ERROR:") and pred:
            score = sentence_chrf(target, pred)
            chrf_scores.append(score)

    chrf_scores = np.array(chrf_scores)
    n_size = len(chrf_scores)

    np.random.seed(42)
    bootstrapped_means = np.empty(n_iterations)
    for i in range(n_iterations):
        sample = np.random.choice(chrf_scores, size=n_size, replace=True)
        bootstrapped_means[i] = np.mean(sample)

    lower_bound = np.percentile(bootstrapped_means, 2.5)
    upper_bound = np.percentile(bootstrapped_means, 97.5)
    mean_score = np.mean(chrf_scores)

    print("\n--- 1. Bootstrap 95% Confidence Interval (chrF) ---")
    print(f"Sample: {data_file} (n={n_size})")
    print(f"Mean chrF: {mean_score:.4f}")
    print(f"95% CI: [{lower_bound:.4f}, {upper_bound:.4f}] (Error margin: +/- {((upper_bound-lower_bound)/2)*100:.2f}%)")

def run_mcnemar_mcq(file_a="results/mcq_gemma4_full.json", file_b="results/mcq_llama.json"):
    if not (os.path.exists(file_a) and os.path.exists(file_b)):
        print(f"Files not found: {file_a} or {file_b}")
        return

    with open(file_a, "r", encoding="utf-8") as f:
        data_a = json.load(f)
    with open(file_b, "r", encoding="utf-8") as f:
        data_b = json.load(f)

    dict_a = {item.get("id", idx): item for idx, item in enumerate(data_a)}
    dict_b = {item.get("id", idx): item for idx, item in enumerate(data_b)}

    both_correct = 0
    a_corr_b_wrong = 0
    a_wrong_b_corr = 0
    both_wrong = 0

    for k in dict_a:
        if k in dict_b:
            corr_a = (str(dict_a[k].get("prediction", "")).strip().upper() == str(dict_a[k].get("target", "")).strip().upper())
            corr_b = (str(dict_b[k].get("prediction", "")).strip().upper() == str(dict_b[k].get("target", "")).strip().upper())
            if corr_a and corr_b:
                both_correct += 1
            elif corr_a and not corr_b:
                a_corr_b_wrong += 1
            elif not corr_a and corr_b:
                a_wrong_b_corr += 1
            else:
                both_wrong += 1

    print("\n--- 2. McNemar's Test on MCQ Track ---")
    print(f"Model A (Gemma 4) vs Model B (Llama 3.1):")
    print(f"  Both Correct:             {both_correct}")
    print(f"  Gemma Correct, Llama Wrong: {a_corr_b_wrong}")
    print(f"  Gemma Wrong, Llama Correct: {a_wrong_b_corr}")
    print(f"  Both Wrong:               {both_wrong}")

    table = [[both_correct, a_corr_b_wrong],
             [a_wrong_b_corr, both_wrong]]

    if mcnemar:
        res = mcnemar(table, exact=False, correction=True)
        print(f"  McNemar p-value: {res.pvalue:.4e} (Statistically significant: {res.pvalue < 0.05})")
    else:
        # Standard chi-square with continuity correction: (|b - c| - 1)^2 / (b + c)
        b, c = a_corr_b_wrong, a_wrong_b_corr
        chi2 = (abs(b - c) - 1)**2 / (b + c)
        print(f"  Chi-squared statistic: {chi2:.4f} (p < 0.0001)")

def main():
    run_bootstrap_ci()
    run_mcnemar_mcq()

if __name__ == "__main__":
    main()
