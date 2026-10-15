"""
Tokenizer Audit Script for Dhivehi-Bench.
Verifies the presence of Thaana script tokens (Unicode range U+0780 - U+07B1)
and computes token fertility on parallel English-Dhivehi benchmark samples.
"""

import json
import re
import os
import argparse
from transformers import AutoTokenizer

THAANA_PATTERN = re.compile(r'[\u0780-\u07B1]')

MODELS = {
    "Qwen2.5-7B": "Qwen/Qwen2.5-7B",
    "Llama-3-8B": "unsloth/llama-3-8b",
    "Gemma-2B": "google/gemma-2b"
}

def audit_vocabulary(tokenizer, model_name):
    vocab = tokenizer.get_vocab()
    thaana_tokens = []
    multi_char_thaana = []

    for token in vocab.keys():
        t_str = token.decode("utf-8", errors="ignore") if isinstance(token, bytes) else token
        if THAANA_PATTERN.search(t_str):
            thaana_tokens.append(t_str)
            clean = re.sub(r"[^\u0780-\u07B1]", "", t_str)
            if len(clean) > 1:
                multi_char_thaana.append(t_str)

    print(f"\n==========================================")
    print(f"Model: {model_name}")
    print(f"Vocabulary Size: {len(vocab):,}")
    print(f"Thaana Tokens Found: {len(thaana_tokens)}")
    print(f"Multi-character Merged Thaana Tokens: {len(multi_char_thaana)}")
    print(f"Byte-Fallback Forced: {'YES (100% of Thaana)' if len(thaana_tokens) == 0 else 'NO'}")
    return len(thaana_tokens)

def compute_fertility(tokenizer, model_name, data_path, num_samples=100):
    if not os.path.exists(data_path):
        print(f"Dataset path {data_path} not found. Skipping fertility computation.")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    sample = data[:num_samples]
    total_en_words = sum(len(x["english"].split()) for x in sample)
    total_dv_words = sum(len(x["target_dhivehi"].split()) for x in sample)

    en_tokens = sum(len(tokenizer.encode(x["english"])) for x in sample)
    dv_tokens = sum(len(tokenizer.encode(x["target_dhivehi"])) for x in sample)

    en_ratio = en_tokens / total_en_words
    dv_ratio = dv_tokens / total_dv_words
    penalty = dv_ratio / en_ratio

    print(f"English: {en_tokens:,} tokens / {total_en_words:,} words ({en_ratio:.2f} tokens/word)")
    print(f"Dhivehi: {dv_tokens:,} tokens / {total_dv_words:,} words ({dv_ratio:.2f} tokens/word)")
    print(f"Tokenization Tax Penalty: {penalty:.2f}x")

def main():
    parser = argparse.ArgumentParser(description="Audit tokenizers for Thaana vocabulary coverage.")
    parser.add_argument("--data", default="results/translation_results.json", help="Path to parallel translation data")
    parser.add_argument("--samples", type=int, default=100, help="Number of sentences for fertility estimation")
    parser.add_argument("--local_only", action="store_true", default=True, help="Use cached models only")
    args = parser.parse_args()

    for name, path in MODELS.items():
        try:
            tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=args.local_only)
            audit_vocabulary(tokenizer, name)
            compute_fertility(tokenizer, name, args.data, args.samples)
        except Exception as e:
            print(f"Could not load {name} from {path}: {e}")

if __name__ == "__main__":
    main()
