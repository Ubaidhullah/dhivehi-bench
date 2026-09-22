import json
import re

INPUT_FILE = "context_qa/data/context_qa_dataset_polished_v2.jsonl"
OUTPUT_FILE = "context_qa/data/context_qa_dataset_polished_v2_fixed.jsonl"

phrases_to_remove = [
    "މި ލިޔުމުގައި ބަޔާންކޮށްފައިވާ ގޮތުގައި",
    "ލިޔުމުގައި ބަޔާންކޮށްފައިވާ ގޮތުގައި",
    "މި ލިޔުމުގައި ބަޔާންކޮށްފައިވާ",
    "ލިޔުމުގައި ބަޔާންކޮށްފައިވާ",
    "މި ލިޔުމުގައިވާ ގޮތުން",
    "ލިޔުމުގައިވާ ގޮތުން",
    "މި ލިޔުމުގައިވާ",
    "ލިޔުމުގައިވާ",
    "މި ލިޔުމުގައި",
    "ލިޔުމުގައި",
    "މި އިބާރާތުގައި",
    "އިބާރާތުގައި"
]

def clean_question(q):
    if not q: return q
    
    # Remove phrases
    for phrase in phrases_to_remove:
        # Match phrase with optional spaces
        q = re.sub(phrase + r'\s*', '', q)
        
    # Capitalize first letter if it got stripped (Not really applicable to Dhivehi, but clean spaces)
    q = re.sub(r'\s+', ' ', q).strip()
    
    # Fix punctuation
    q = q.replace('?', '؟')
    q = q.replace(',', '،')
    q = q.replace(';', '؛')
    q = re.sub(r'؟+', '؟', q)
    
    if q and not q.endswith('؟'):
        if q.endswith('.'):
            q = q[:-1] + '؟'
        else:
            q += '؟'
            
    return q

def clean_answer(a):
    if not a: return a
    a = re.sub(r'\s+', ' ', a).strip()
    a = a.replace('?', '؟')
    a = a.replace(',', '،')
    a = a.replace(';', '؛')
    return a

fixed_count = 0
data = []
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    for line in f:
        row = json.loads(line)
        
        # ONLY touch unconfirmed rows
        if row.get("status") != "confirmed":
            orig_q = row.get("question", "")
            orig_a = row.get("answer", "")
            
            new_q = clean_question(orig_q)
            new_a = clean_answer(orig_a)
            
            if new_q != orig_q or new_a != orig_a:
                row["question"] = new_q
                row["answer"] = new_a
                fixed_count += 1
                
        data.append(row)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for row in data:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

import shutil
shutil.move(OUTPUT_FILE, INPUT_FILE)

print(f"Removed 'According to text' references & fixed punctuation in {fixed_count} unconfirmed QA pairs!")
