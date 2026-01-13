import os
import json
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from tqdm import tqdm

DIRECTORIES_TO_PROCESS = [
    './papers',
    './papers_missing_ms'
]

def set_paragraph_rtl(paragraph):
    """Sets paragraph to Right-to-Left and Right Aligned."""
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    pPr = paragraph._element.get_or_add_pPr()
    bidi = OxmlElement('w:bidi')
    # According to MS-DOCX schema, bidi should come before jc (alignment)
    # but python-docx's get_or_add_pPr might put jc first.
    # To be safe and compliant with what worked before:
    pPr.insert(0, bidi)

def set_run_font(run, font_name):
    """Sets the font of a run, including complex scripts."""
    run.font.name = font_name
    # Handle East Asia/Complex Script fonts in XML
    r = run._element
    rPr = r.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn('w:ascii'), font_name)
    rFonts.set(qn('w:hAnsi'), font_name)
    rFonts.set(qn('w:cs'), font_name)
    
    # Enable RTL for the run if it's Dhivehi
    if font_name == 'Faruma':
        run.font.rtl = True

def add_paragraph(doc, text, font_name):
    """Adds a formatted paragraph with specific font and RTL settings."""
    p = doc.add_paragraph()
    set_paragraph_rtl(p)
    run = p.add_run(text)
    set_run_font(run, font_name)
    return p

def process_json_file(json_path):
    """Converts a single JSON file to DOCX."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        doc = Document()
        
        articles = data.get('articles', [])
        for a_idx, article in enumerate(articles, 1):
            # [article_<n>]
            add_paragraph(doc, f"[article_{a_idx}]", 'Arial')
            
            # <article title>
            title = article.get('title')
            if title:
                add_paragraph(doc, title, 'Faruma')
                
            # <article body>
            add_paragraph(doc, article.get('content', ''), 'Faruma')
            
            # Questions
            questions = article.get('questions', [])
            for q_idx, question in enumerate(questions, 1):
                q_type = question.get('type', 'unknown')
                
                # [article_<n>_question_<m>_<type>]
                add_paragraph(doc, f"[article_{a_idx}_question_{q_idx}_{q_type}]", 'Arial')
                
                # <question text>
                add_paragraph(doc, question.get('text', ''), 'Faruma')
                
                # Answer
                answer = question.get('answer')
                if answer:
                    # [article_<n>_question_<m>_answer]
                    add_paragraph(doc, f"[article_{a_idx}_question_{q_idx}_answer]", 'Arial')
                    add_paragraph(doc, answer, 'Faruma')
                
                # Extra line after each question-answer pair
                doc.add_paragraph()
            
            # Summary
            summary = article.get('summary')
            if summary:
                # [article_<n>_summary]
                add_paragraph(doc, f"[article_{a_idx}_summary]", 'Arial')
                add_paragraph(doc, summary, 'Faruma')
            
            # Extra line after each article
            doc.add_paragraph()

        output_path = json_path.replace('.json', ' processed.docx')
        doc.save(output_path)
        return True
    except Exception as e:
        print(f"Error processing {json_path}: {e}")
        return False

def main():
    json_files = []
    for root_dir in DIRECTORIES_TO_PROCESS:
        if not os.path.exists(root_dir):
            continue
        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if filename.lower().endswith('.json'):
                    json_files.append(os.path.join(dirpath, filename))
                    
    print(f"Found {len(json_files)} JSON files to process.")
    for f in tqdm(json_files, desc="Converting JSON to DOCX"):
        process_json_file(f)

if __name__ == "__main__":
    main()
