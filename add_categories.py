import json
import os
import glob

# Map pdf filenames to their category folder
pdf_to_category = {}
saruna_dir = "mcq/data/saruna"
for root, dirs, files in os.walk(saruna_dir):
    for f in files:
        if f.endswith(".pdf"):
            category = os.path.basename(root)
            pdf_to_category[f] = category

input_file = "mcq/data/mcq_dataset_v2.jsonl"
output_file = "mcq/data/mcq_dataset_categorized.jsonl"

total = 0
mapped = 0

with open(input_file, "r", encoding="utf-8") as f_in, open(output_file, "w", encoding="utf-8") as f_out:
    for line in f_in:
        try:
            data = json.loads(line)
            total += 1
            txt_name = data.get("source_file", "")
            pdf_name = txt_name.replace(".txt", ".pdf")
            
            category = pdf_to_category.get(pdf_name, "Unknown")
            data["category"] = category
            if category != "Unknown":
                mapped += 1
            
            f_out.write(json.dumps(data, ensure_ascii=False) + "\n")
        except:
            pass

print(f"Total MCQs: {total}")
print(f"Mapped to categories: {mapped}")
