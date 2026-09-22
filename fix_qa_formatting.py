import json
import re

INPUT_FILE = "context_qa/data/context_qa_dataset_polished_v2.jsonl"
OUTPUT_FILE = "context_qa/data/context_qa_dataset_polished_v2_fixed.jsonl"

def clean_dhivehi_text(text):
    if not text:
        return text
    
    # 1. Replace English punctuation with Arabic/Dhivehi punctuation
    text = text.replace('?', '؟')
    text = text.replace(',', '،')
    text = text.replace(';', '؛')
    
    # 2. Fix spacing around punctuation
    text = re.search(r'\s+؟', '؟').string if ' ؟' in text else text
    text = text.replace(' ؟', '؟')
    text = text.replace(' ،', '،')
    text = text.replace(' ؛', '؛')
    text = text.replace(' .', '.')
    
    # 3. Remove multiple sequential question marks
    text = re.sub(r'؟+', '؟', text)
    
    # 4. Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def fix_question_string(q):
    q = clean_dhivehi_text(q)
    # Ensure it ends with a Dhivehi question mark
    if q and not q.endswith('؟'):
        # If it ends with a full stop, replace it
        if q.endswith('.'):
            q = q[:-1] + '؟'
        else:
            q += '؟'
    return q

fixed_count = 0
total_unconfirmed = 0

data = []
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    for line in f:
        row = json.loads(line)
        
        # Only touch unconfirmed ones
        if row.get("status") != "confirmed":
            total_unconfirmed += 1
            
            orig_q = row.get("question", "")
            orig_a = row.get("answer", "")
            
            new_q = fix_question_string(orig_q)
            new_a = clean_dhivehi_text(orig_a)
            
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

print(f"Total unconfirmed rows checked: {total_unconfirmed}")
print(f"Automatically fixed formatting in {fixed_count} QA pairs!")
