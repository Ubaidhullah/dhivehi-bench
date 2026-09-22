import os
import pypdf
import csv
import re
from tqdm import tqdm

ASSESSMENT_FILE = "mcq/data/pdf_assessment.csv"
OUTPUT_DIR = "mcq/data/extracted_text"

def clean_text(text):
    # Basic cleaning
    text = re.sub(r'\s+', ' ', text) # Normalize whitespace
    return text.strip()

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    print("Extracting text from searchable PDFs...")
    
    with open(ASSESSMENT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        searchable_pdfs = [row for row in reader if row["is_searchable"] == "True"]
    
    for row in tqdm(searchable_pdfs):
        path = row["path"]
        filename = row["filename"]
        txt_filename = os.path.splitext(filename)[0] + ".txt"
        txt_path = os.path.join(OUTPUT_DIR, txt_filename)
        
        try:
            reader = pypdf.PdfReader(path)
            full_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            cleaned = clean_text(full_text)
            if cleaned:
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(cleaned)
        except Exception as e:
            print(f"Error extracting {filename}: {e}")

    print(f"\nExtraction complete. Files saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
