import os
import pypdf

DIRECTORIES_TO_PROCESS = [
    './papers',
    './papers_missing_ms'
]

def extract_text_from_pdf(pdf_path):
    text_content = []
    try:
        reader = pypdf.PdfReader(pdf_path)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return None

    return "\n".join(text_content)

def main():
    empty_files = []
    processed_count = 0
    
    print("Starting PDF text extraction...")

    for root_dir in DIRECTORIES_TO_PROCESS:
        if not os.path.exists(root_dir):
            print(f"Directory not found: {root_dir}")
            continue

        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if filename.lower().endswith('.pdf'):
                    pdf_path = os.path.join(dirpath, filename)
                    txt_path = os.path.splitext(pdf_path)[0] + '.txt'
                    
                    print(f"Processing: {pdf_path}")
                    
                    extracted_text = extract_text_from_pdf(pdf_path)
                    
                    if extracted_text and extracted_text.strip():
                        try:
                            with open(txt_path, 'w', encoding='utf-8') as f:
                                f.write(extracted_text)
                            processed_count += 1
                        except Exception as e:
                            print(f"Error writing to {txt_path}: {e}")
                    else:
                        print(f"WARNING: No text extracted from {pdf_path}")
                        empty_files.append(pdf_path)

    print("\n" + "="*40)
    print(f"Extraction Complete.")
    print(f"Processed: {processed_count} files.")
    
    if empty_files:
        print("\n[REPORT] Files with NO extracted text (likely scanned images):")
        for f in empty_files:
            print(f" - {f}")
    else:
        print("\nAll processed PDFs yielded text.")

if __name__ == '__main__':
    main()
