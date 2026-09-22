import json
import uuid

input_file = "context_qa/data/context_qa_dataset.jsonl"
output_file = "context_qa/data/context_qa_dataset_curated.jsonl"

with open(input_file, "r", encoding="utf-8") as fin, open(output_file, "w", encoding="utf-8") as fout:
    for line in fin:
        data = json.loads(line)
        if "id" not in data:
            data["id"] = str(uuid.uuid4())
        fout.write(json.dumps(data, ensure_ascii=False) + "\n")
