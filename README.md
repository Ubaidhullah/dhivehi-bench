# Dhivehi Bench

**Dhivehi Bench** is a comprehensive project designed to create benchmark datasets for the Dhivehi language. It aims to support various Natural Language Processing (NLP) tasks, enabling better evaluation and development of Dhivehi language models.

<!-- TOC -->
* [Dhivehi Bench](#dhivehi-bench)
  * [Project Scope](#project-scope)
  * [Sub-Projects](#sub-projects)
    * [1. Translation Module](#1-translation-module)
    * [2. MCQ Module](#2-mcq-module)
    * [3. Context QA Module](#3-context-qa-module)
<!-- TOC -->

## Project Scope

The project consists of three distinct, highly-curated sub-modules, each focusing on a specific benchmark domain:

1.  **Translation** (Completed)
    -   **Completed**: 2,000 high-quality parallel samples.
    -   **Source**: Presidency and independent news articles.
    -   **Verification**: All samples have been manually verified and refined by skilled Dhivehi translators to ensure benchmark-grade accuracy.
2.  **MCQ Question Answering** (Completed)
    -   **Completed**: 2,070 multiple-choice questions for testing reasoning and knowledge.
    -   **Source**: Extracted via Qwen2.5-VL OCR from MNU Digital Repository (Saruna) across 9 academic domains.
    -   **Verification**: Categorized using semantic LLM classifiers and manually curated.
3.  **Context-Based Question Answering** (Completed)
    -   **Completed**: 1,134 high-quality SQuAD-style QA pairs spanning 303 unique documents.
    -   **Source**: Extracted via Qwen2.5-VL OCR from diverse Dhivehi domains (History, Law, Essays) and manually curated/polished.
    -   **Verification**: Manually verified via a custom curation UI to enforce standalone benchmarking rules.

---

## Sub-Projects

Each module is self-contained with its own scripts and `requirements.txt`.

### 1. Translation Module

Located in: `./translation/`

This module focuses on creating a high-quality parallel corpus for English-Dhivehi translation.

#### Dataset Details

- **Size**: 2,000 parallel sentence pairs.
- **Source**: News articles from the President's Office (Presidency) and independent news outlets.
- **Quality Assurance**: Every pair has been manually verified and refined by skilled Dhivehi translators to ensure high semantic fidelity and grammatical correctness.

#### Alignment Tool

The project includes a custom **Dhivehi-English Alignment Engine** located in `./translation/dhivehi-english-alignment-engine/`. This tool uses Gemini models to assist in the initial semantic alignment of comparable documents before human review.

---

### 2. MCQ Module

Located in: `./mcq/`

This module scrapes Dhivehi content for MCQ dataset generation.

#### Setup

```bash
cd mcq
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

#### Data Source: Saruna (MNU Digital Repository)

The primary data source is [Saruna](https://saruna.mnu.edu.mv), the Maldives National University's digital repository. It runs on DSpace 8.0 and provides an excellent REST API.

**API Documentation:** https://saruna.mnu.edu.mv/server/api

Key endpoints:
- `GET /server/api/core/collections/{uuid}` - Collection info
- `GET /server/api/discover/search/objects?scope={uuid}` - Search within collection
- `GET /server/api/core/items/{uuid}/bundles` - Item bundles
- `GET /server/api/core/bitstreams/{uuid}/content` - Download file

#### Scripts

**Saruna Scraper (`scrapers/saruna_scraper.py`)**

Downloads PDFs from a Saruna collection.

```bash
# Download 10 pages from Dhivehi Language Studies collection
python scrapers/saruna_scraper.py ffb9e093-5a2b-42fa-a584-2aa19d7d5e7d --pages 10

# Download all pages
python scrapers/saruna_scraper.py ffb9e093-5a2b-42fa-a584-2aa19d7d5e7d --pages 0

# Custom output directory
python scrapers/saruna_scraper.py <collection_id> --pages 5 --output ./my_data
```

Find collection IDs by browsing https://saruna.mnu.edu.mv/communities - the UUID is in the URL.

---

### 3. Context QA Module

Located in: `./context_qa/`

This module generates SQuAD-style reading comprehension datasets to evaluate Dhivehi language models.

#### Dataset Details

- **Size**: 1,134 SQuAD-style QA pairs based on 574 unique paragraphs.
- **Source**: Extracted from various PDFs via Qwen2.5-VL and parsed locally.
- **Quality Assurance**: Automatically scrubbed of hallucinated formatting, normalized using a robust Gemini polishing prompt, and meticulously verified via a manual Streamlit curation UI to enforce standalone benchmarking rules.
