# Dhivehi-Bench 🇲🇻

[![Hugging Face Datasets](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Datasets-yellow)](https://huggingface.co/datasets/ubaidhullah05/dhivehi-bench)
[![License: MIT](https://img.shields.io/badge/Code%20License-MIT-blue.svg)](LICENSE)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/Data%20License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

**Dhivehi-Bench** is the first comprehensive, contamination-mitigated evaluation benchmark designed for the Dhivehi language (written in the right-to-left Thaana script). By combining custom OCR digitization of offline historical archives with multi-stage human native post-editing and unanimous consensus verification, Dhivehi-Bench establishes an empirical foundation across three distinct tracks:

1. **Multiple Choice Reasoning (MCQ):** 2,070 items testing semantic reading comprehension across 9 authentic academic domains.
2. **Contextual Question Answering (Context QA):** 1,134 SQuAD-style extractive comprehension items derived from digitized national archives.
3. **Bidirectional Translation:** 2,016 parallel sentence pairs (EN$\rightarrow$DV and DV$\rightarrow$EN) evaluating generative fluency and receptive bilingualism.

> **Note on Availability:** This repository and the associated Hugging Face dataset will be made fully public upon publication.

---

## 🚀 Quickstart: Load from Hugging Face

The full benchmark is hosted on Hugging Face Datasets: [`ubaidhullah05/dhivehi-bench`](https://huggingface.co/datasets/ubaidhullah05/dhivehi-bench).

You can load each evaluation track with the `datasets` Python library:

```bash
pip install datasets
```

```python
from datasets import load_dataset

# 1. Multiple-Choice Reasoning Track (2,070 items)
mcq_dataset = load_dataset("ubaidhullah05/dhivehi-bench", "mcq")
print("MCQ sample:", mcq_dataset["test"][0])

# 2. Contextual Question Answering Track (1,134 items)
qa_dataset = load_dataset("ubaidhullah05/dhivehi-bench", "squad")
print("QA sample:", qa_dataset["test"][0])

# 3. Bidirectional Translation Track (2,016 parallel pairs)
translation_dataset = load_dataset("ubaidhullah05/dhivehi-bench", "translation")
print("Translation sample:", translation_dataset["test"][0])
```

---

## 🔬 Reproducing the Tokenization Tax & Vocabulary Coverage

Modern foundation LLMs exhibit severe generative breakdown on Dhivehi despite strong reading comprehension. As shown in Section 4.2 of our paper, this failure is rooted in tokenization architecture: modern LLM tokenizers contain **zero learned multi-character merges** for Thaana, shattering words into byte-level sequences.

### Counting Criterion
A vocabulary entry is classified as a Thaana-supported token if and only if its decoded UTF-8 byte representation contains at least one codepoint in the official Thaana Unicode block: **`U+0780` to `U+07BF`**. A multi-character merge is defined as any token whose decoded bytes represent two or more Thaana codepoints.

### Run Verification Script
To reproduce Table 2 from the paper with pinned tokenizer revisions:

```bash
python3 scripts/verify_tokenizers.py
```

### Empirical Coverage (Paper Section 4.2 / Table 2)

| Model | Tokenizer Family | Base Vocab | Effective Vocab | Thaana Tokens | Multi-Char Merges | Fallback Rate |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Gemma 4 (31B)** | SentencePiece | 256,000 | 262,144* | 42 | **0** | **100% (Fallback)** |
| **Llama 3.1 (70B)** | Tiktoken BPE | 128,000 | 128,256 | 0 | **0** | **100% (Fallback)** |
| **Qwen 2.5 (72B)** | Tiktoken BPE | 151,643 | 152,064 | 8† | **0** | **100% (Fallback)** |

- `*` Gemma 4's base SentencePiece vocabulary is 256,000. In the Gemma Technical Report, the output projection matrix is dimensioned to $d \times 262,144$ ($2^{18}$, $\approx 262\text{k}$) in the Multi-Token Prediction (MTP) specification for TPU/GPU alignment.
- `†` Qwen 2.5 contains 8 isolated single-consonant characters without vowel diacritics (*fili*); because continuous written Dhivehi requires vowel diacritics, all continuous text forces byte fallback.
- **Key Result:** Across all three frontier models, learned multi-character Thaana merges are exactly **zero**, forcing 100% byte-level fallback that inflates token fertility up to **21.12 tokens/word** (a 16.5x penalty).

---

## 📁 Repository Structure & Sub-Projects

```
dhivehi-bench/
├── mcq/                                 # MCQ track scraping, generation & curation
│   ├── scrapers/saruna_scraper.py      # DSpace 8.0 REST API scraper for MNU Saruna
│   └── data/                            # Curated MCQ splits
├── context_qa/                          # Contextual QA track (SQuAD-style)
│   └── data/                            # OCR-digitized archival QA pairs
├── translation/                         # Translation track & alignment engine
│   ├── dhivehi-english-alignment-engine/# Multi-stage LLM alignment pipeline
│   └── data/                            # 2,016 parallel pairs (EN-DV / DV-EN)
├── scripts/
│   └── verify_tokenizers.py             # Reproducible tokenizer & vocabulary verification
├── paper/
│   ├── main.tex                         # Complete LaTeX manuscript
│   ├── references.bib                   # BibTeX bibliographic entries
│   └── fig_tokenization.pdf             # Tokenization tax diagram (Figure 2)
└── README.md
```

### 1. Translation Module (`./translation/`)
- **Dataset Size:** 2,016 parallel sentence and paragraph pairs.
- **Sources:** Official Presidency communiqués, the Constitution of the Maldives, and professionally translated administrative literature.
- **Quality Assurance:** Unanimous consensus across an independent panel of three native Maldivian speakers.
- **Alignment Engine:** Custom pipeline using frontier LLM ensembles (`./translation/dhivehi-english-alignment-engine/`) for initial candidate alignment prior to manual verification.

### 2. MCQ Module (`./mcq/`)
- **Dataset Size:** 2,070 four-way multiple-choice items spanning 9 academic domains.
- **Source:** Extracted from non-machine-readable historical archives at [Saruna](https://saruna.mnu.edu.mv) (Maldives National University DSpace repository) using custom Viyavi OCR.
- **Scraper Usage:**
  ```bash
  cd mcq
  python scrapers/saruna_scraper.py ffb9e093-5a2b-42fa-a584-2aa19d7d5e7d --pages 10 --output ./data
  ```
- **Distractor Hardening:** 64.2% of candidate distractors manually rewritten by native speakers with morphologically similar grammatical traps.

### 3. Context QA Module (`./context_qa/`)
- **Dataset Size:** 1,134 extractive SQuAD-style QA pairs over 574 unique archival contexts.
- **Anti-Contamination:** Built exclusively on offline historical manuscripts digitized via custom OCR.
- **Evaluation:** Evaluated using Exact Match (EM) and Token F1, accommodating Dhivehi's agglutinative morphology.

---

## 📜 Citation

If you use Dhivehi-Bench in your research, please cite:

```bibtex
@article{dhivehibench2026,
  title={Dhivehi-Bench: A Comprehensive Benchmark for Evaluating Large Language Models on the Maldivian Language},
  author={Hameed, Ubaidhullah Abdul},
  journal={ACM Transactions on Asian and Low-Resource Language Information Processing (TALLIP)},
  year={2026}
}
```

---

## 📄 License
- **Code & Scripts:** Licensed under the [MIT License](LICENSE).
- **Benchmark Datasets:** Licensed under the [Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/) license.
