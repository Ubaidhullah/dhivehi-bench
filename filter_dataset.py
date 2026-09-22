import json
import re
from collections import Counter

INPUT_FILE = "context_qa/data/context_qa_dataset_curated.jsonl"
OUTPUT_FILE = "context_qa/data/context_qa_dataset_filtered.jsonl"

def is_bad_paragraph(text):
    if not text or len(text.strip()) < 20:
        return True, "Too short"
        
    total_chars = len(text)
    
    # 1. Check English (A-Z, a-z)
    english_chars = len(re.findall(r'[A-Za-z]', text))
    if english_chars / total_chars > 0.05: # > 5% English
        return True, "Too much English"
        
    # 2. Check Arabic (U+0600 to U+06FF) - Thaana is U+0780 to U+07BF
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    if arabic_chars / total_chars > 0.15: # > 15% Arabic
        return True, "Too much Arabic"
        
    # 3. Check for severe repetition (character level)
    # e.g., "މމމމމމ"
    if re.search(r'(.)\1{7,}', text):
        return True, "Repeated characters"
        
    # 4. Check for hallucinated word loops (e.g., "ދިޔަ ދިޔަ ދިޔަ ދިޔަ")
    words = text.split()
    if len(words) > 10:
        word_counts = Counter(words)
        most_common_word, count = word_counts.most_common(1)[0]
        # Ignore common stop words for this simple metric, just check if a single word dominates 30% of the text
        if count / len(words) > 0.3 and len(most_common_word) > 2:
            return True, "Word repetition loop"
            
    return False, ""

data = []
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    for line in f:
        data.append(json.loads(line))

# We filter based on the CONTEXT. If context is bad, drop all QA pairs for it.
dropped_reasons = Counter()
filtered_data = []

unique_contexts = {d['context'] for d in data}
bad_contexts = set()

for ctx in unique_contexts:
    is_bad, reason = is_bad_paragraph(ctx)
    if is_bad:
        bad_contexts.add(ctx)
        dropped_reasons[reason] += 1

for d in data:
    if d['context'] not in bad_contexts:
        filtered_data.append(d)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for d in filtered_data:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")

print(f"Total Original QA Pairs: {len(data)}")
print(f"Total Filtered QA Pairs: {len(filtered_data)}")
print(f"Dropped {len(data) - len(filtered_data)} pairs.")
print("\nDrop Reasons (by unique context):")
for reason, count in dropped_reasons.items():
    print(f"- {reason}: {count} paragraphs")

