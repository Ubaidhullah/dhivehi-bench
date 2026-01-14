# Dhivehi-English Alignment Engine

This application utilizes Google's Gemini models to perform the challenging task of semantically aligning Dhivehi and English texts.

**Purpose:** This tool is designed strictly for **bitext alignment**—extracting semantically equivalent sentence pairs from noisy, comparable documents. 

> ### ⚠️ Mandatory Human Verification
> To produce high-quality datasets suitable for machine learning benchmarks, **manual human verification of every aligned pair is mandatory**. While Gemini is powerful, AI models can hallucinate, misinterpret cultural nuances, or create "near-matches" that do not meet benchmark standards. **Do not use the raw output without review.**

## Features

* **Semantic Alignment:** Aligns content based on meaning rather than direct translation.
* **JSONL Output:** Generates structured JSON Lines data for easy integration into ML pipelines.
* **Streamlit UI:** A clean, minimal web interface for pasting text and visualizing results.
* **CLI Support:** A command-line interface for batch processing or scripting.

## Getting Started

### Prerequisites

* **Python 3.8+**
* A valid **Google Gemini API Key**

### Installation

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Environment:**
    Create a `.env` or `.env.local` file in the root directory and add your API key:
    ```env
    API_KEY=your_api_key_here
    ```

### Usage

#### Option 1: Web Interface (Streamlit)
Run the visual interface to paste text and download results interactively.

```bash
streamlit run app.py
```

#### Option 2: Command Line Interface (CLI)
Run the alignment script directly from the terminal.

```bash
# Interactive mode (prompts for input)
python align.py

# File mode
python align.py --english-file en.txt --dhivehi-file dv.txt --output aligned.json
```

### Project Structure

* `app.py`: The Streamlit web application.
* `align.py`: Core logic script for text alignment using Gemini.
* `requirements.txt`: Python dependencies.
