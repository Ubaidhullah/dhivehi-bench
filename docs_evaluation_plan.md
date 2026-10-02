# Dhivehi Bench: Evaluation Methodology

This document outlines the comprehensive strategy for evaluating Large Language Models (LLMs) on Dhivehi Bench, designed for publication in a CCF-C or CCF-B tier NLP venue.

## 1. Selected Open-Source Models

Given the hardware constraints (1x NVIDIA RTX 4090 with 24GB VRAM), we will focus on evaluating highly capable open-weight models in the 7B to 14B parameter range at `bfloat16` precision (or up to 30B using INT4 quantization).

### Baseline Models
*   **Llama 3.1 (8B)**: The industry standard baseline for open-weight models. Although heavily English-centric, it serves as a baseline for cross-lingual transfer.
*   **Qwen 2.5 (7B & 14B)**: Highly recommended. Qwen models possess exceptionally strong multilingual capabilities and have historically shown strong zero-shot transfer to underrepresented languages. 
*   **Gemma 2 (9B)**: Google's open-weight model, known for punching above its weight class in reasoning and logic.
*   **Mistral NeMo (12B)**: A joint release by Mistral and NVIDIA with a 128k context window and a highly optimized tokenizer that is very efficient for non-Latin scripts.
*   **Aya 23 (8B)**: Cohere's massively multilingual model. While Dhivehi might not be in its core training set, its extreme multilingual alignment makes it a crucial test subject for zero-shot transfer.

*Note: All models will be served using `vLLM` or `lm-evaluation-harness` to maximize GPU utilization on the RTX 4090.*

---

## 2. Evaluation Framework

We will use **EleutherAI's `lm-evaluation-harness`**. 
This is the absolute gold standard for NLP benchmarking papers. It guarantees reproducibility and allows us to test 0-shot, 1-shot, and 5-shot configurations out-of-the-box. We will write custom YAML task definitions for Dhivehi Bench to plug directly into the harness.

---

## 3. Task Methodologies & Metrics

Each track requires a distinct evaluation methodology to prevent prompt-engineering biases and generation parsing errors.

### Track A: Multiple Choice Questions (Knowledge & Reasoning)
*   **Methodology:** **Log-Likelihood Evaluation**. 
    *   *How it works:* Instead of asking the model to generate text (e.g., "Answer A") and attempting to parse the output, we feed the model the Question and calculate the raw log-likelihood probabilities of the model generating Option A, Option B, Option C, and Option D. The option with the highest probability is selected as the model's prediction.
    *   *Why:* This completely eliminates formatting errors (e.g., the model refusing to answer or chatting back) and purely measures the model's internal belief distribution.
*   **Metrics:** Accuracy (%).
*   **Settings:** 0-shot and 5-shot.

### Track B: Contextual QA (Reading Comprehension / SQuAD)
*   **Methodology:** **Generative QA**.
    *   *How it works:* The model is provided with the Dhivehi paragraph (Context) and the Question. It is prompted to generate a short, extractive answer.
*   **Metrics:** 
    *   **Token F1 Score:** Measures the overlap of words/tokens between the generated answer and the ground-truth answer (accounting for partial correctness).
    *   **ROUGE-L:** Measures the longest common subsequence, ensuring the structural flow of the answer matches the truth.
    *   **Exact Match (EM):** A strict metric measuring if the generation perfectly matches the ground truth (useful as a baseline, though often too harsh for generative models).
*   **Settings:** 0-shot and 1-shot.

### Track C: Machine Translation (Parallel Corpus)
*   **Methodology:** **Generative Translation (En-Dv and Dv-En)**.
    *   *How it works:* The model is prompted to translate an English sentence to Dhivehi, and vice versa. 
*   **Metrics:** 
    *   **chrF / chrF++ (Character n-gram F-score):** *Crucial for Dhivehi.* Because Dhivehi is a morphologically rich language (words change based on tense, gender, and status), standard word-level metrics fail. chrF evaluates at the character level, perfectly capturing root words even if suffixes change. (Used by IndicBench).
    *   **BLEU (sacreBLEU):** The traditional word-overlap baseline required by all NLP papers.
*   **Settings:** 5-shot (Translation models rely heavily on few-shot examples to lock into the target language).

---

## 4. Execution Plan (Next Steps)

1. **Finalize Curation:** Complete the MCQ curation using the new UI.
2. **Compile Datasets:** Script the compilation of all 3 datasets into HuggingFace `datasets` format (`.jsonl`).
3. **Write YAML Harness:** Write the 3 custom `lm-evaluation-harness` task configurations.
4. **Run Benchmark:** Spin up the RTX 4090, download the models (Llama 3, Qwen 2.5), and execute the harness.
