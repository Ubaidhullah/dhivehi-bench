# MCQ Module Implementation Plan

This document outlines the step-by-step procedure for generating a Multiple Choice Question (MCQ) benchmark dataset for Dhivehi.

## Phase 1: Data Acquisition (Scraping)
The primary source of data is **Saruna** (MNU Digital Repository).

1.  **Identify Target Collections**: Use the Saruna communities page to find relevant collection UUIDs. Current scope includes:
    -   Dhivehi Language Studies
    -   Maldivian History
    -   Maldivian Art & Culture
    -   Religion
    -   Poetry
    -   Essays
    -   Science
    -   Shari'ah & Law
    -   Political Science
    -   Education
    -   Customs & Traditions
2.  **Execute Scraper**: Run `mcq/scrapers/bulk_scrape.sh` or `mcq/scrapers/retry_scrape.sh`.
3.  **Verify Downloads**: Check `mcq/data/saruna/<Collection_Name>_downloads.csv` to ensure high success rate.

## Phase 2: Pre-processing & OCR (Advanced)
Many documents in Saruna are scanned PDFs. We utilize a fine-tuned **Qwen 2.5 3B** model for superior Dhivehi OCR.

1.  **Google Colab Setup**: Use the provided `mcq/Dhivehi_OCR_Qwen_Colab.ipynb` notebook.
2.  **Model Loading**: Load the fine-tuned Qwen 2.5 3B model from Google Drive.
3.  **OCR Processing**:
    -   Convert PDF pages to images.
    -   Perform inference using the Qwen model to extract accurate Dhivehi text.
    -   Save extracted text back to Google Drive (`mcq/data/extracted_text`).
4.  **Text Cleaning**: Normalize Thaana characters and segment text for the next phase.

## Phase 3: MCQ Generation (AI-Assisted)
Use LLMs (**Gemini 3 or higher**) to generate high-quality MCQs from the extracted text. These models provide superior understanding of Dhivehi context and nuances.

1.  **Develop Prompt Template**: Create a robust prompt that instructs the LLM to:
    - Identify a key fact or concept in the text.
    - Formulate a clear question in Dhivehi.
    - Provide one correct answer and three plausible distractors.
    - Ensure all options are culturally and linguistically appropriate.
2.  **Batch Processing**: Script the generation process using the Gemini API.
3.  **Initial Schema**: Save as JSONL with the following format:
    ```json
    {
      "context": "...",
      "question": "...",
      "options": ["A", "B", "C", "D"],
      "answer": "A",
      "metadata": {"source": "...", "collection": "..."}
    }
    ```

## Phase 4: Human Verification & Refinement
**Crucial Step**: Machine-generated questions must be reviewed.

1.  **Review Criteria**:
    - Is the question factually correct based on the context?
    - Are the distractors effective and not obviously wrong?
    - Is the Dhivehi grammar and vocabulary natural and academic?
2.  **Refinement**: Translators/subject matter experts edit the questions and options.
3.  **Final Polish**: Ensure consistent formatting across the entire dataset.

## Phase 5: Finalization & Integration
1.  **Format Conversion**: Export the final verified dataset to standard formats (JSONL, CSV).
2.  **Documentation**: Update the main README.md with MCQ dataset statistics.
3.  **Backup**: Ensure all scripts and final data are committed/pushed to the private repository.
