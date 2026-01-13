import os
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv
from tqdm import tqdm
from enum import Enum

# Load environment variables from parent directory
load_dotenv(dotenv_path="../.env")

# Configuration
DIRECTORIES_TO_PROCESS = [
    './papers',
    './papers_missing_ms'
]
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found in .env file.")
else:
    print(f"API Key found (Length: {len(GEMINI_API_KEY)})")

client = genai.Client(api_key=GEMINI_API_KEY)

class QuestionType(str, Enum):
    EXTRACTIVE = 'extractive'
    ABSTRACTIVE = 'abstractive'

# Pydantic Models for Structured Output
class Question(BaseModel):
    text: str = Field(description="The text of the question, omitting question number and marks.")
    answer: Optional[str] = Field(description="The answer to the question from the marking scheme. Leave blank if not available.")
    type: QuestionType = Field(description="The type of the question (extractive or abstractive).")

class Article(BaseModel):
    title: Optional[str] = Field(description="The title for the article if available..")
    content: str = Field(description="The full text content of the article.")
    summary: Optional[str] = Field(description="A brief summary of the article if available in the marking scheme.")
    questions: List[Question] = Field(description="A list of questions extracted for this article.")
    keywords: List[str] = Field(description="A list of English keywords that broadly describe the article's content..")
    category: str = Field(description="The category of the article in English (e.g. 'History', 'Health', etc.)")

class ExtractionResult(BaseModel):
    articles: List[Article] = Field(description="A list of articles extracted from the paper.")

def extract_content(paper_text: str, ms_text: str) -> ExtractionResult:
    """Uses Gemini to extract structured articles and questions."""
    model_name = 'gemini-3-pro-preview'
    prompt = f"""
    You are an expert at processing Dhivehi exam papers. 
    Analyze the provided Question Paper and its corresponding Marking Scheme (if available).
    
    Extract all articles and their associated questions. 
    
    Constraints:
    - Extract the full text of each article.
    - Extract questions related to each article. 
    - Omit question numbers and marks from the question text.
    - Skip questions that require multiple articles to answer.
    - For each question, extract the corresponding answer from the marking scheme. If no marking scheme is provided, leave it blank.
    - If a summary of the article is provided in the marking scheme, extract it.
    - Only extract articles for the reading comprehension and summarization tasks.
    
    Question Paper Text:
    {paper_text}
    
    Marking Scheme Text:
    {ms_text if ms_text else "No marking scheme provided."}
    """

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=ExtractionResult,
            ),
        )

        return response.parsed
    except Exception as e:
        print(f"API Call failed: {e}")
        raise

def identify_pairs():
    """Identifies Question Paper and Marking Scheme pairs."""
    pairs = []
    
    for root_dir in DIRECTORIES_TO_PROCESS:
        if not os.path.exists(root_dir):
            continue
            
        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if filename.lower().endswith('.txt') and not filename.lower().endswith('marking scheme.txt'):
                    paper_path = os.path.join(dirpath, filename)
                    paper_name = filename[:-4] # Remove .txt
                    
                    ms_filename = f"{paper_name} Marking Scheme.txt"
                    ms_path = os.path.join(dirpath, ms_filename)
                    
                    if not os.path.exists(ms_path):
                        ms_path = None
                        
                    output_path = os.path.join(dirpath, f"{paper_name}.json")
                    
                    pairs.append({
                        "name": paper_name,
                        "paper_path": paper_path,
                        "ms_path": ms_path,
                        "output_path": output_path
                    })
    return pairs

def process_paper(pair):
    """Processes a single paper-MS pair."""
    try:
        with open(pair["paper_path"], 'r', encoding='utf-8') as f:
            paper_text = f.read()
            
        ms_text = ""
        if pair["ms_path"]:
            with open(pair["ms_path"], 'r', encoding='utf-8') as f:
                ms_text = f.read()
                
        result = extract_content(paper_text, ms_text)
        
        with open(pair["output_path"], 'w', encoding='utf-8') as f:
            json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)
            
        return True
    except Exception as e:
        print(f"Error processing {pair['name']}: {e}")
        return False

def main():
    pairs = identify_pairs()
    print(f"Found {len(pairs)} papers to process.")
    
    for pair in tqdm(pairs, desc="Extracting Articles"):
        process_paper(pair)

if __name__ == "__main__":
    main()
