# Dhivehi Bench

**Dhivehi Bench** is a comprehensive project designed to create benchmark datasets for the Dhivehi language. It aims to support various Natural Language Processing (NLP) tasks, enabling better evaluation and development of Dhivehi language models.

<!-- TOC -->
* [Dhivehi Bench](#dhivehi-bench)
  * [Project Scope](#project-scope)
  * [Sub-Projects](#sub-projects)
    * [1. Summarization Module](#1-summarization-module)
    * [2. MCQ Module](#2-mcq-module)
    * [3. Translation Module](#3-translation-module)
<!-- TOC -->

## Project Scope

The project consists of several distinct sub-modules, each focusing on a specific benchmark domain:

1.  **Summarization** (Active)
    -   Collection and processing of documents for abstractive and extractive summarization.
2.  **Translation** (Active)
    -   **Completed**: 2,000 high-quality parallel samples.
    -   **Source**: Presidency and independent news articles.
    -   **Verification**: All samples have been manually verified and refined by skilled Dhivehi translators to ensure benchmark-grade accuracy.
3.  **MCQ Question Answering** (Active)
    -   Multiple-choice datasets for testing reasoning and knowledge.
4.  **Context-Based Question Answering** (Completed)
    -   **Completed**: 1,134 high-quality SQuAD-style QA pairs spanning 574 unique paragraphs.
    -   **Source**: Extracted via Qwen2.5-VL OCR from diverse Dhivehi domains (History, Law, Essays) and manually curated/polished.

---

## Sub-Projects

Each module is self-contained with its own scripts and `requirements.txt`.

### 1. Summarization Module

Located in: `./summarization/`

This module focuses on processing DPE (Department of Public Examinations) past papers to create text resources.

#### Setup

1.  **Navigate to directory**:
    ```bash
    cd summarization
    ```

2.  **Create and Activate Virtual Environment**:
    It is highly recommended to use a virtual environment.
    ```bash
    # Create venv
    python -m venv venv

    # Activate (Windows)
    .\venv\Scripts\activate

    # Activate (Mac/Linux)
    source venv/bin/activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

#### Scripts

**1. Downloader (`dpe_downloader.py`)**
-   **Usage**: `python dpe_downloader.py`
-   **Purpose**: Downloads paired Question Papers (QP) and Marking Schemes (MS) from `dpe.html`.
-   **Output**: folders `./papers/` (paired) and `./papers_missing_ms/` (unpaired).

**2. PDF Text Extractor (`pdf_extractor.py`)**
-   **Usage**: `python pdf_extractor.py`
-   **Purpose**: Extracts raw text from the downloaded PDFs using `pypdf`.
-   **Output**: `.txt` files in the same directories.

**3. DOCX Converter (`txt_to_docx.py`)**
-   **Usage**: `python txt_to_docx.py`
-   **Purpose**: Converts extracted text to properly formatted DOCX files.
-   **Features**:
    -   Applies **Faruma** font.
    -   Ensures **RTL** (Right-to-Left) direction.
    -   Applies **Right Alignment**.

**4. Content Validator (`check_thaana.py`)**
-   **Usage**: `python check_thaana.py`
-   **Purpose**: Scans text files to identify those missing Thaana characters (e.g., failed OCR or English-only documents).

**5. Article Extractor (`article_extractor.py`)**
-   **Usage**: `python article_extractor.py`
-   **Purpose**: Uses **Gemini 3 Pro Preview** (synchronous) to extract structured JSON data.
-   **Output**: `<Paper Name>.json` containing articles, questions, answers, and summaries.

**6. JSON to DOCX Converter (`json_to_docx.py`)**
-   **Usage**: `python json_to_docx.py`
-   **Purpose**: Converts the structured JSON files into formatted "processed" DOCX files.
-   **Features**:
    -   **RTL** and **Right Aligned** text.
    -   **Faruma** font for content.
    -   **Arial** font for metadata markers (e.g., `[article_1]`).
-   **Output**: `<Paper Name> processed.docx`.

#### Workflow

To generate the summarization dataset section:
1.  Run `dpe_downloader.py` to get the raw data.
2.  Run `pdf_extractor.py` to digitize the content.
3.  Run `check_thaana.py` to validate quality.
4.  Run `txt_to_docx.py` to finalize formatting.

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

### 3. Translation Module

Located in: `./translation/`

This module focuses on creating a high-quality parallel corpus for English-Dhivehi translation.

#### Dataset Details

- **Size**: 2,000 parallel sentence pairs.
- **Source**: News articles from the President's Office (Presidency) and independent news outlets.
- **Quality Assurance**: Every pair has been manually verified and refined by skilled Dhivehi translators to ensure high semantic fidelity and grammatical correctness.

#### Alignment Tool

The project includes a custom **Dhivehi-English Alignment Engine** located in `./translation/dhivehi-english-alignment-engine/`. This tool uses Gemini models to assist in the initial semantic alignment of comparable documents before human review.


---

### 4. Context QA Module

Located in: `./context_qa/`

This module generates SQuAD-style reading comprehension datasets to evaluate Dhivehi language models.

#### Dataset Details

- **Size**: 1,134 SQuAD-style QA pairs based on 574 unique paragraphs.
- **Source**: Extracted from various PDFs via Qwen2.5-VL and parsed locally.
- **Quality Assurance**: Automatically scrubbed of hallucinated formatting, normalized using a robust Gemini polishing prompt, and meticulously verified via a manual Streamlit curation UI to enforce standalone benchmarking rules.
