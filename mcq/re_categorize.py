import json
import concurrent.futures
from collections import defaultdict
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

GEMINI_API_KEY = "AQ.Ab8RN6IYCuYrtd8rRDmoEiaTcoys8kvZShxFCCE70SBdFRn2MQ"
client = genai.Client(api_key=GEMINI_API_KEY)

class ClassificationResult(BaseModel):
    category: str = Field(description="The most appropriate category for the document.")

ALLOWED_CATEGORIES = [
    "Maldivian_History",
    "Religion_and_Islam",
    "Shariah_Law",
    "Political_Science",
    "Dhivehi_Language_Studies",
    "Art_and_Culture",
    "Literature_and_Poetry",
    "Science_and_Geography",
    "General_Knowledge"
]

def classify_document(filename, sample_mcqs):
    prompt = f"""
    You are an expert content classifier for a Dhivehi language benchmark.
    Analyze the following document title and a few sample multiple-choice questions extracted from it.
    
    Document Title: {filename}
    
    Sample Questions:
    {sample_mcqs}
    
    Classify the core subject of this document into EXACTLY ONE of the following categories:
    {', '.join(ALLOWED_CATEGORIES)}
    
    Return the result as JSON.
    """
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=ClassificationResult,
                temperature=0.1
            ),
        )
        return response.parsed.category
    except Exception as e:
        print(f"Error classifying {filename}: {e}")
        return None

def main():
    input_file = "mcq/data/mcq_dataset_categorized.jsonl"
    output_file = "mcq/data/mcq_dataset_categorized_updated.jsonl"
    
    # 1. Group MCQs by source_file
    grouped_mcqs = defaultdict(list)
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            grouped_mcqs[data.get("source_file", "Unknown")].append(data)
            
    print(f"Loaded {sum(len(v) for v in grouped_mcqs.values())} MCQs across {len(grouped_mcqs)} unique documents.")
    
    # 2. Classify each document
    new_categories = {}
    
    def process_file(filename, mcq_list):
        # We only need the first 3 questions to get the gist of the topic
        samples = ""
        for i, mcq in enumerate(mcq_list[:3]):
            samples += f"Q{i+1}: {mcq.get('question', '')}\nAnswer Explanation: {mcq.get('explanation', '')}\n\n"
            
        category = classify_document(filename, samples)
        if category not in ALLOWED_CATEGORIES:
            category = "General_Knowledge" # fallback
        return filename, category

    print("Starting classification...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_file = {executor.submit(process_file, fname, mlist): fname for fname, mlist in grouped_mcqs.items()}
        completed = 0
        for future in concurrent.futures.as_completed(future_to_file):
            fname, category = future.result()
            new_categories[fname] = category
            completed += 1
            if completed % 20 == 0:
                print(f"Classified {completed}/{len(grouped_mcqs)} documents...")
                
    # 3. Write out the updated dataset
    updated_count = 0
    with open(output_file, "w", encoding="utf-8") as f:
        # We will iterate through original files to maintain exactly the same data structure
        for fname, mcq_list in grouped_mcqs.items():
            cat = new_categories.get(fname, "General_Knowledge")
            for mcq in mcq_list:
                mcq["category"] = cat
                f.write(json.dumps(mcq, ensure_ascii=False) + "\n")
                updated_count += 1
                
    print(f"\nSuccessfully re-categorized and saved {updated_count} MCQs to {output_file}!")

if __name__ == "__main__":
    main()
