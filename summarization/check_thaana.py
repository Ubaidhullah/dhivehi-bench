import os

DIRECTORIES_TO_PROCESS = [
    './papers',
    './papers_missing_ms'
]

def has_thaana(text):
    for char in text:
        if '\u0780' <= char <= '\u07BF':
            return True
    return False

def main():
    non_thaana_files = []
    
    print("Checking for Thaana characters in text files...")
    
    for root_dir in DIRECTORIES_TO_PROCESS:
        if not os.path.exists(root_dir):
            continue
            
        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if filename.lower().endswith('.txt'):
                    txt_path = os.path.join(dirpath, filename)
                    
                    try:
                        with open(txt_path, 'r', encoding='utf-8') as f:
                            text = f.read()
                            
                        # If file is empty, it also strictly lacks Thaana
                        if not has_thaana(text):
                            non_thaana_files.append(txt_path)
                            
                    except Exception as e:
                        print(f"Error reading {txt_path}: {e}")

    print("\n" + "="*40)
    print(f"Check Complete.")
    
    if non_thaana_files:
        print(f"Found {len(non_thaana_files)} files WITHOUT Thaana characters:")
        for f in non_thaana_files:
            print(f" - {f}")
    else:
        print("All text files contain Thaana characters.")

if __name__ == '__main__':
    main()
