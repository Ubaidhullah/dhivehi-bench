# Dhivehi Bench

**Dhivehi Bench** is a comprehensive project designed to create benchmark datasets for the Dhivehi language. It aims to support various Natural Language Processing (NLP) tasks, enabling better evaluation and development of Dhivehi language models.

<!-- TOC -->
* [Dhivehi Bench](#dhivehi-bench)
  * [Project Scope](#project-scope)
  * [Sub-Projects](#sub-projects)
    * [1. Summarization Module](#1-summarization-module)
      * [Setup](#setup)
      * [Scripts](#scripts)
      * [Workflow](#workflow)
<!-- TOC -->

## Project Scope

The project consists of several distinct sub-modules, each focusing on a specific benchmark domain:

1.  **Summarization** (Active)
    -   Collection and processing of documents for abstractive and extractive summarization.
2.  **Translation** (Planned)
    -   Parallel corpus creation for English-Dhivehi translation.
3.  **MCQ Question Answering** (Planned)
    -   Multiple-choice datasets for testing reasoning and knowledge.
4.  **Context-Based Question Answering** (Planned)
    -   Reading comprehension datasets based on provided contexts.

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

#### Workflow

To generate the summarization dataset section:
1.  Run `dpe_downloader.py` to get the raw data.
2.  Run `pdf_extractor.py` to digitize the content.
3.  Run `check_thaana.py` to validate quality.
4.  Run `txt_to_docx.py` to finalize formatting.
