import os
import pypdf
import csv
from tqdm import tqdm

DATA_DIR = "mcq/data/saruna"
OUTPUT_REPORT = "mcq/data/pdf_assessment.csv"

def assess_pdf(path):
    try:
        reader = pypdf.PdfReader(path)
        num_pages = len(reader.pages)
        text_content = ""
        # Check first 5 pages for text
        for i in range(min(5, num_pages)):
            page_text = reader.pages[i].extract_text()
            if page_text:
                text_content += page_text
        
        has_text = len(text_content.strip()) > 50 # Heuristic for meaningful text
        return num_pages, has_text
    except Exception as e:
        return 0, False

def main():
    results = []
    print("Assessing PDFs for extractable text...")
    
    pdf_files = []
    for root, dirs, files in os.walk(DATA_DIR):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, file))
    
    for path in tqdm(pdf_files):
        num_pages, has_text = assess_pdf(path)
        results.append({
            "path": path,
            "filename": os.path.basename(path),
            "pages": num_pages,
            "is_searchable": has_text
        })
    
    with open(OUTPUT_REPORT, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "filename", "pages", "is_searchable"])
        writer.writeheader()
        writer.writerows(results)
    
    searchable_count = sum(1 for r in results if r["is_searchable"])
    print(f"\nAssessment Complete:")
    print(f"Total PDFs: {len(results)}")
    print(f"Searchable (Native): {searchable_count}")
    print(f"Scanned (Requires OCR): {len(results) - searchable_count}")
    print(f"Report saved to: {OUTPUT_REPORT}")

if __name__ == "__main__":
    main()
