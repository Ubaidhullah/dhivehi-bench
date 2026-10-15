import json
import sys
import os
import re

def compute_f1(pred: str, gold: str):
    pred_tokens = re.findall(r'\S+', pred.strip())
    gold_tokens = re.findall(r'\S+', gold.strip())
    if not pred_tokens or not gold_tokens:
        return 1.0 if pred_tokens == gold_tokens else 0.0
    
    common = {}
    for t in pred_tokens:
        if t in gold_tokens:
            common[t] = common.get(t, 0) + 1
    
    num_same = sum(min(pred_tokens.count(t), gold_tokens.count(t)) for t in set(pred_tokens))
    if num_same == 0:
        return 0.0
    
    precision = num_same / len(pred_tokens)
    recall = num_same / len(gold_tokens)
    return (2 * precision * recall) / (precision + recall)

def compute_em(pred: str, gold: str):
    return 1.0 if pred.strip().lower() == gold.strip().lower() else 0.0

def compute_cohens_kappa(eval1_answers, eval2_answers, num_options=4):
    # For MCQ
    n = len(eval1_answers)
    if n == 0:
        return 0.0
    agreed = sum(1 for k in eval1_answers if eval1_answers[k] == eval2_answers.get(k))
    po = agreed / n
    
    # Expected agreement pe
    categories = ['A', 'B', 'C', 'D']
    pe = 0.0
    for cat in categories:
        p1 = sum(1 for k in eval1_answers if eval1_answers[k] == cat) / n
        p2 = sum(1 for k in eval2_answers if eval2_answers.get(k) == cat) / n
        pe += p1 * p2
        
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 score_human_eval.py <evaluator1.json> [evaluator2.json]")
        sys.exit(1)
        
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gold_file = os.path.join(base_dir, "human_eval_pack", "gold_answers.json")
    
    with open(gold_file, "r", encoding="utf-8") as f:
        gold_data = json.load(f)
        
    gold_mcq = gold_data["mcq"]
    gold_qa = gold_data["context_qa"]
    
    eval_files = sys.argv[1:]
    eval_results = []
    
    for fpath in eval_files:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            eval_results.append(data)
            
    print("=" * 60)
    print(" 🇲🇻 DHIVEHI-BENCH HUMAN BASELINE EVALUATION REPORT")
    print("=" * 60)
    
    scores = []
    for idx, e in enumerate(eval_results, 1):
        name = e.get("reviewer_name", f"Evaluator {idx}")
        mcq_answers = e.get("mcq_answers", {})
        qa_answers = e.get("qa_answers", {})
        
        # Score MCQ
        mcq_correct = 0
        mcq_total = len(gold_mcq)
        for q_id, gold_info in gold_mcq.items():
            if mcq_answers.get(q_id) == gold_info["answer"]:
                mcq_correct += 1
        mcq_acc = (mcq_correct / mcq_total) * 100
        
        # Score Contextual QA
        f1_scores = []
        em_scores = []
        for q_id, gold_info in gold_qa.items():
            pred_text = qa_answers.get(q_id, "")
            gold_text = gold_info["answer"]
            f1_scores.append(compute_f1(pred_text, gold_text))
            em_scores.append(compute_em(pred_text, gold_text))
            
        avg_f1 = (sum(f1_scores) / len(f1_scores)) * 100 if f1_scores else 0.0
        avg_em = (sum(em_scores) / len(em_scores)) * 100 if em_scores else 0.0
        
        scores.append({
            "name": name,
            "mcq_acc": mcq_acc,
            "mcq_answers": mcq_answers,
            "f1": avg_f1,
            "em": avg_em
        })
        
        print(f"\n[{name}]")
        print(f"  • MCQ Accuracy (100 items):    {mcq_acc:.2f}% ({mcq_correct}/{mcq_total})")
        print(f"  • Contextual QA Token F1:     {avg_f1:.2f}%")
        print(f"  • Contextual QA Exact Match:  {avg_em:.2f}%")

    if len(scores) >= 2:
        mean_mcq = (scores[0]["mcq_acc"] + scores[1]["mcq_acc"]) / 2
        mean_f1 = (scores[0]["f1"] + scores[1]["f1"]) / 2
        mean_em = (scores[0]["em"] + scores[1]["em"]) / 2
        kappa = compute_cohens_kappa(scores[0]["mcq_answers"], scores[1]["mcq_answers"])
        
        print("\n" + "=" * 60)
        print(" 📊 COMBINED HUMAN BASELINE SUMMARY (Table 2 & Section 5.5)")
        print("=" * 60)
        print(f"  • MCQ Accuracy:               {mean_mcq:.2f}% (Eval 1: {scores[0]['mcq_acc']:.1f}%, Eval 2: {scores[1]['mcq_acc']:.1f}%)")
        print(f"  • Contextual QA Token F1:     {mean_f1:.2f}%")
        print(f"  • Contextual QA Exact Match:  {mean_em:.2f}%")
        print(f"  • Inter-Annotator Agreement:  Cohen's κ = {kappa:.2f}")
        print("\nReady-to-paste Table 2 row:")
        print(f"\\textit{{Human Baseline ($n=200$ stratified)}} & \\textit{{{mean_mcq:.2f}}} & \\textit{{{mean_f1:.2f}}} & \\textit{{{mean_em:.2f}}} & \\textit{{--}} & \\textit{{--}} & \\textit{{--}} & \\textit{{--}} \\\\")
    print("=" * 60)

if __name__ == "__main__":
    main()
