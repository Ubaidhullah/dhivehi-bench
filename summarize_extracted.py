import os
import glob
from collections import Counter

saruna_dir = "mcq/data/saruna"
extracted_dir = "mcq/data/extracted_text"

# 1. Map pdf filename -> Category
pdf_to_category = {}
for root, dirs, files in os.walk(saruna_dir):
    for f in files:
        if f.endswith(".pdf"):
            category = os.path.basename(root)
            pdf_to_category[f] = category

# 2. Count extracted text files by category
category_counts = Counter()
extracted_files = glob.glob(os.path.join(extracted_dir, "*.txt"))

unmapped = 0
for filepath in extracted_files:
    filename = os.path.basename(filepath)
    pdf_name = filename.replace(".txt", ".pdf")
    
    cat = pdf_to_category.get(pdf_name)
    if cat:
        category_counts[cat] += 1
    else:
        unmapped += 1

print("--- SUMMARY OF ALL 1,175 EXTRACTED FILES ---")
for cat, count in category_counts.most_common():
    print(f"- {cat}: {count} files")

if unmapped > 0:
    print(f"\nUnmapped/Unknown files: {unmapped}")
