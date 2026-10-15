import json
import random
import os

SEED = 42
random.seed(SEED)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_DIR = os.path.join(BASE_DIR, "human_eval_pack")
os.makedirs(PACK_DIR, exist_ok=True)

# 1. Stratified sample 100 MCQs
with open(os.path.join(BASE_DIR, "results", "mcq_dataset_rebalanced.json"), "r", encoding="utf-8") as f:
    mcqs = json.load(f)

# Group by category
mcq_by_cat = {}
for m in mcqs:
    cat = m.get("category", "General")
    mcq_by_cat.setdefault(cat, []).append(m)

sampled_mcqs = []
total_mcq = len(mcqs)
for cat, items in sorted(mcq_by_cat.items()):
    cat_target = max(1, round(len(items) / total_mcq * 100))
    random.shuffle(items)
    sampled_mcqs.extend(items[:cat_target])

# Trim or pad to exactly 100
random.shuffle(sampled_mcqs)
sampled_mcqs = sampled_mcqs[:100]

# 2. Stratified sample 100 SQuAD items
with open(os.path.join(BASE_DIR, "context_qa", "data", "dhivehi_squad.jsonl"), "r", encoding="utf-8") as f:
    squads = [json.loads(line.strip()) for line in f if line.strip()]

squad_by_cat = {}
for s in squads:
    cat = s.get("category", "General")
    squad_by_cat.setdefault(cat, []).append(s)

sampled_squad = []
total_squad = len(squads)
for cat, items in sorted(squad_by_cat.items()):
    cat_target = max(1, round(len(items) / total_squad * 100))
    random.shuffle(items)
    sampled_squad.extend(items[:cat_target])

random.shuffle(sampled_squad)
sampled_squad = sampled_squad[:100]

print(f"Sampled {len(sampled_mcqs)} MCQs and {len(sampled_squad)} Contextual QA items.")

# Separate blind test items and gold answers
blind_mcqs = []
gold_mcqs = {}
for idx, m in enumerate(sampled_mcqs, 1):
    q_id = f"mcq_{idx}"
    blind_mcqs.append({
        "id": q_id,
        "num": idx,
        "category": m.get("category", "General"),
        "question": m["question"],
        "options": m["options"]
    })
    gold_mcqs[q_id] = {
        "answer": m["answer"],
        "options": m["options"],
        "question": m["question"]
    }

blind_squad = []
gold_squad = {}
for idx, s in enumerate(sampled_squad, 1):
    q_id = f"qa_{idx}"
    blind_squad.append({
        "id": q_id,
        "num": idx,
        "category": s.get("category", "General"),
        "context": s["context"],
        "question": s["question"]
    })
    gold_squad[q_id] = {
        "answer": s["answer"],
        "question": s["question"]
    }

test_pack = {
    "mcq": blind_mcqs,
    "context_qa": blind_squad
}

gold_pack = {
    "mcq": gold_mcqs,
    "context_qa": gold_squad
}

with open(os.path.join(PACK_DIR, "test_items.json"), "w", encoding="utf-8") as f:
    json.dump(test_pack, f, ensure_ascii=False, indent=2)

with open(os.path.join(PACK_DIR, "gold_answers.json"), "w", encoding="utf-8") as f:
    json.dump(gold_pack, f, ensure_ascii=False, indent=2)

print("Saved test_items.json and gold_answers.json in human_eval_pack/")
