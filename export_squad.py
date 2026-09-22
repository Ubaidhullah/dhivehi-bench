import json

input_file = "context_qa/data/context_qa_dataset_polished_v2.jsonl"
output_file = "context_qa/data/dhivehi_squad.jsonl"

confirmed = 0
with open(input_file, "r", encoding="utf-8") as fin, open(output_file, "w", encoding="utf-8") as fout:
    for line in fin:
        data = json.loads(line)
        if data.get("status") == "confirmed":
            # Remove the status key for the final export
            if "status" in data:
                del data["status"]
            fout.write(json.dumps(data, ensure_ascii=False) + "\n")
            confirmed += 1

print(f"Exported {confirmed} QA pairs to {output_file}")
