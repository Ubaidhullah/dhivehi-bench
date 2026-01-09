import os
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml.shared import OxmlElement

DIRECTORIES_TO_PROCESS = [
    './papers',
    './papers_missing_ms'
]

def create_docx_from_text(txt_path, docx_path):
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        print(f"Error reading {txt_path}: {e}")
        return False

    document = Document()
    
    # Add a paragraph with the text
    paragraph = document.add_paragraph()
    
    # Set Alignment
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    run = paragraph.add_run(text)
    
    # Set Font Details
    font = run.font
    font.name = 'Faruma'
    font.size = Pt(12)
    font.rtl = True
    
    # Vital for some complex scripts in Word to pick up the right font
    rPr = run._r.get_or_add_rPr()
    
    # Set complex script font to Faruma
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn('w:cs'), 'Faruma')
    
    try:
        document.save(docx_path)
        return True
    except Exception as e:
        print(f"Error saving {docx_path}: {e}")
        return False

def main():
    processed_count = 0
    print("Starting TXT to DOCX conversion...")
    
    for root_dir in DIRECTORIES_TO_PROCESS:
        if not os.path.exists(root_dir):
            continue
            
        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if filename.lower().endswith('.txt'):
                    txt_path = os.path.join(dirpath, filename)
                    docx_path = os.path.splitext(txt_path)[0] + '.docx'
                    
                    print(f"Converting: {txt_path}")
                    if create_docx_from_text(txt_path, docx_path):
                        processed_count += 1
                        
    print("\n" + "="*40)
    print(f"Conversion Complete.")
    print(f"Converted: {processed_count} files.")

if __name__ == '__main__':
    main()
