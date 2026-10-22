import json
import os
import sys
from collections import Counter

CATEGORIES = [
    "particle_loops",
    "code_switching",
    "incoherent_hallucination",
    "synonymy_register",
    "fluent_translation"
]

CATEGORY_NAMES = {
    "particle_loops": "Morphological / Repetition Loop",
    "code_switching": "English Code-Switching",
    "incoherent_hallucination": "Incoherent / Hallucination",
    "synonymy_register": "Synonym / Register Variation",
    "fluent_translation": "Fluent & Accurate Translation"
}


def compute_cohens_kappa(ratings_1: dict, ratings_2: dict, item_ids: list):
    n = len(item_ids)
    if n == 0:
        return 0.0, 0.0, 0.0, {}

    agree = sum(1 for k in item_ids if ratings_1[k] == ratings_2[k])
    p_o = agree / n

    counts_1 = Counter(ratings_1[k] for k in item_ids)
    counts_2 = Counter(ratings_2[k] for k in item_ids)

    p_e = sum((counts_1[c] / n) * (counts_2[c] / n) for c in CATEGORIES)
    kappa = (p_o - p_e) / (1.0 - p_e) if (1.0 - p_e) > 0 else 1.0

    matrix = {c1: {c2: 0 for c2 in CATEGORIES} for c1 in CATEGORIES}
    for k in item_ids:
        matrix[ratings_1[k]][ratings_2[k]] += 1

    return kappa, p_o, p_e, matrix


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/score_romanized_eval.py <annotator1.json> <annotator2.json>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        d1 = json.load(f)
    with open(sys.argv[2], "r", encoding="utf-8") as f:
        d2 = json.load(f)

    r1 = d1.get("ratings", {})
    r2 = d2.get("ratings", {})

    shared_ids = sorted(k for k in r1.keys() if k in r2 and r1[k] in CATEGORIES and r2[k] in CATEGORIES)
    if not shared_ids:
        print("Error: No shared coded items found between the two JSON files.")
        sys.exit(1)

    kappa, p_o, p_e, matrix = compute_cohens_kappa(r1, r2, shared_ids)

    combined_counts = Counter()
    for k in shared_ids:
        combined_counts[r1[k]] += 1
        combined_counts[r2[k]] += 1

    total_votes = 2 * len(shared_ids)
    percentages = {
        c: round((combined_counts[c] / total_votes) * 100, 1) for c in CATEGORIES
    }

    print("=" * 70)
    print(f"Dhivehi-Bench Section 5.7 Romanized Transliteration Audit (n = {len(shared_ids)})")
    print("=" * 70)
    print(f"Annotator 1: {d1.get('annotator', 'Coder 1')}")
    print(f"Annotator 2: {d2.get('annotator', 'Coder 2')}")
    print(f"Observed Agreement (P_o): {p_o * 100:.2f}% ({sum(1 for k in shared_ids if r1[k] == r2[k])}/{len(shared_ids)} items)")
    print(f"Expected Chance Agreement (P_e): {p_e * 100:.2f}%")
    print(f"Cohen's Kappa (κ): {kappa:.2f} ({kappa:.4f})")
    print("-" * 70)
    print("Category Distribution (Averaged across both annotators):")
    for c in CATEGORIES:
        c1_cnt = sum(1 for k in shared_ids if r1[k] == c)
        c2_cnt = sum(1 for k in shared_ids if r2[k] == c)
        print(
            f"  - {CATEGORY_NAMES[c]:32s}: {percentages[c]:5.1f}%  "
            f"(A1: {c1_cnt:2d}, A2: {c2_cnt:2d})"
        )
    print("=" * 70)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_path = os.path.join(base_dir, "results", "romanized_eval_audit.json")
    report = {
        "n_items": len(shared_ids),
        "annotator_1": d1.get("annotator", "Annotator 1"),
        "annotator_2": d2.get("annotator", "Annotator 2"),
        "observed_agreement": round(p_o, 4),
        "chance_agreement": round(p_e, 4),
        "cohens_kappa": round(kappa, 4),
        "distribution_percentages": percentages,
        "confusion_matrix": matrix
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Audit report saved to: {out_path}")


if __name__ == "__main__":
    main()
