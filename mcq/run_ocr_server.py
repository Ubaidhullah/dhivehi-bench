import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, PaliGemmaForConditionalGeneration, PaliGemmaProcessor
import fitz
from PIL import Image
from tqdm import tqdm

# ==========================================
# CONFIGURATION - UPDATE THESE PATHS
# ==========================================
# Path to your downloaded Qwen Checkpoint on the server
QWEN_CHECKPOINT = "./checkpoint-10000"
PALIGEMMA_MODEL = "google/paligemma-3b-pt-224"

# Paths to data
INPUT_DIR = "./mcq/data/saruna"
OUTPUT_DIR = "./mcq/data/extracted_text"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Load Models
print("Loading Qwen 2.5 Base Model...")
from peft import PeftModel
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
from qwen_vl_utils import process_vision_info

base_model_name = "unsloth/Qwen2.5-VL-3B-Instruct" # We'll use the unquantized or normal version since unsloth allows merging

processor = AutoProcessor.from_pretrained(base_model_name, trust_remote_code=True)
base_model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    base_model_name,
    device_map="auto",
    torch_dtype=torch.bfloat16,
    trust_remote_code=True
)

print("Applying Fine-Tuned LoRA Adapter...")
model = PeftModel.from_pretrained(base_model, QWEN_CHECKPOINT)
model.eval()

# 2. Layout Detection (Placeholder layout logic)
def detect_layout(image):
    # Placeholder: Assuming full image for now
    return [image]

# 3. Main OCR Logic
def perform_ocr(pdf_path):
    doc = fitz.open(pdf_path)
    images = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    doc.close()
    
    full_text = ""
    
    for page_img in images:
        segments = detect_layout(page_img)
        
        for segment_img in segments:
            temp_img_path = "/tmp/temp_segment.jpg"
            segment_img.save(temp_img_path)
            
            try:
                # Qwen2.5-VL Inference
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "image": temp_img_path},
                            {"type": "text", "text": "Extract the Dhivehi text from this image."},
                        ],
                    }
                ]
                text = processor.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
                image_inputs, video_inputs = process_vision_info(messages)
                inputs = processor(
                    text=[text],
                    images=image_inputs,
                    videos=video_inputs,
                    padding=True,
                    return_tensors="pt",
                ).to(model.device)
                
                with torch.no_grad():
                    generated_ids = model.generate(**inputs, max_new_tokens=1024)
                    generated_ids_trimmed = [
                        out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
                    ]
                
                response = processor.batch_decode(
                    generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
                )[0]
                
                full_text += response.strip() + "\n"
            except Exception as e:
                print(f"Error processing segment: {e}")
                
        full_text += "\n"
    return full_text

# 4. Processing Loop
pdf_files = []
for root, dirs, files in os.walk(INPUT_DIR):
    for file in files:
        if file.lower().endswith(".pdf"):
            pdf_files.append(os.path.join(root, file))

print(f"Found {len(pdf_files)} PDFs to process.")

for pdf_path in tqdm(pdf_files, desc="OCR Processing"):
    filename = os.path.basename(pdf_path)
    txt_path = os.path.join(OUTPUT_DIR, os.path.splitext(filename)[0] + ".txt")
    
    if os.path.exists(txt_path):
        continue # Skip already extracted files
        
    try:
        text = perform_ocr(pdf_path)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        print(f"Failed to process {filename}: {e}")
