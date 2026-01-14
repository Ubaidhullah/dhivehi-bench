import os
import json
import argparse
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()
load_dotenv(".env.local")

def align_text(api_key, id_start, source, domain, english_text, dhivehi_text):
    client = genai.Client(api_key=api_key)

    system_instruction = """You are a "Bitext Miner" for a high-quality Dhivehi-English translation benchmark. 
Your goal is to extract ONLY the semantically equivalent sentence pairs from two noisy, comparable documents and discard everything else.

THE CHALLENGE:
The input documents are "Comparable," not "Parallel." 
- The English text often contains extra explanations, definitions, or context (e.g., "The Maldivian parliament, known as the Majlis...") not present in the Dhivehi text.
- The Dhivehi text may contain local details omitted in the English version.
- The sentence order might differ.

YOUR ALGORITHM:
1. Segmentation: Split both inputs into individual sentences.
2. Search & Align: For every English sentence, scan the Dhivehi text for a semantic match.
    - Strict Match: The meaning is identical (human translation). -> KEEP.
    - Loose/Paraphrase Match: The meaning is preserved, but wording differs. -> KEEP (Preserve exact original text from both sides).
    - Context/Explanation: If the English sentence contains an explanation not in Dhivehi or vice-versa -> DISCARD.
    - No Match: If a sentence has no corresponding translation -> DISCARD.
3. Validation: Ensure the extracted pairs are 1-to-1. Do not merge sentences unless absolutely necessary for meaning.
4. ID Generation: Format is {SOURCE}_{ID_SEQUENCE}. Start the sequence from START_ID.

Return ONLY a JSON array of objects."""

    prompt = f"""
START_ID: {id_start}
SOURCE: {source}
DOMAIN: {domain}
EN_TEXT: {english_text}
DV_TEXT: {dhivehi_text}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3-pro-preview", 
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema={
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "id": {"type": "STRING"},
                            "translation": {
                                "type": "OBJECT",
                                "properties": {
                                    "en": {"type": "STRING"},
                                    "dv": {"type": "STRING"}
                                },
                                "required": ["en", "dv"]
                            },
                            "domain": {"type": "STRING"},
                            "source": {"type": "STRING"}
                        },
                        "required": ["id", "translation", "domain", "source"]
                    }
                },
                thinking_config=types.ThinkingConfig(include_thoughts=False)
            )
        )

        if not response.text:
             raise ValueError("The Bitext Miner failed to produce an output.")
        
        return json.loads(response.text)

    except Exception as e:
        print(f"Error during alignment: {e}", file=sys.stderr)
        return None

def get_multiline_input(prompt):
    print(prompt + " (Press Ctrl+D or Ctrl+Z on new line to finish):")
    contents = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        contents.append(line)
    return "\n".join(contents)

def main():
    parser = argparse.ArgumentParser(description="Dhivehi-English Bitext Miner")
    parser.add_argument("--source", default="unknown", help="Source identifier")
    parser.add_argument("--domain", default="general", help="Domain identifier")
    parser.add_argument("--id-start", type=int, default=1, help="Starting ID sequence")
    parser.add_argument("--english-file", help="Path to English text file")
    parser.add_argument("--dhivehi-file", help="Path to Dhivehi text file")
    parser.add_argument("--output", help="Output JSON file path")

    args = parser.parse_args()

    api_key = os.getenv("API_KEY")
    if not api_key:
        print("Error: API_KEY not found in environment variables or .env file.", file=sys.stderr)
        sys.exit(1)

    # Get English Text
    english_text = ""
    if args.english_file:
        try:
            with open(args.english_file, 'r', encoding='utf-8') as f:
                english_text = f.read()
        except Exception as e:
            print(f"Error reading English file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        english_text = get_multiline_input("Enter English Text")

    # Get Dhivehi Text
    dhivehi_text = ""
    if args.dhivehi_file:
        try:
            with open(args.dhivehi_file, 'r', encoding='utf-8') as f:
                dhivehi_text = f.read()
        except Exception as e:
            print(f"Error reading Dhivehi file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        dhivehi_text = get_multiline_input("Enter Dhivehi Text")

    if not english_text.strip() or not dhivehi_text.strip():
        print("Error: Both English and Dhivehi texts are required.", file=sys.stderr)
        sys.exit(1)

    print("\nMining bitext pairs... Please wait.")
    results = align_text(api_key, args.id_start, args.source, args.domain, english_text, dhivehi_text)

    if results:
        output_json = json.dumps(results, indent=2, ensure_ascii=False)
        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(output_json)
                print(f"Successfully saved results to {args.output}")
            except Exception as e:
                 print(f"Error writing output file: {e}", file=sys.stderr)
                 print(output_json)
        else:
            print("\n--- Results ---")
            print(output_json)

if __name__ == "__main__":
    main()
