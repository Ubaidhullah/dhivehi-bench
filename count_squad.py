import json

file_path = "context_qa/data/context_qa_dataset_polished_v2.jsonl"
confirmed_pairs = 0
unique_contexts = set()

with open(file_path, 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        if data.get("status") == "confirmed":
            confirmed_pairs += 1
            unique_contexts.add(data["context"])

print(f"Confirmed QA Pairs: {confirmed_pairs}")
print(f"Unique Paragraphs: {len(unique_contexts)}")
