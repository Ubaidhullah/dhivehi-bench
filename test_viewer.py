import streamlit as st
import re

st.set_page_config(layout="wide", page_title="Test Samples Viewer")

artifact_path = "/Users/ubaidhullahhameed/.gemini/antigravity-cli/brain/ba90f708-8b3d-41f1-8317-e820154596cc/prompt_test_results.md"

def load_samples():
    with open(artifact_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    samples = []
    # Split by "## Sample "
    parts = content.split("## Sample ")[1:]
    for part in parts:
        lines = part.split("\n")
        title_line = lines[0]
        
        orig_match = re.search(r"### Original \(Corrupted\)\n> (.*?)\n\n### Cleaned", part, re.DOTALL)
        clean_match = re.search(r"### Cleaned \(New Prompt\)\n> (.*?)\n\n---", part, re.DOTALL)
        
        if orig_match and clean_match:
            samples.append({
                "title": title_line,
                "original": orig_match.group(1).strip(),
                "cleaned": clean_match.group(1).strip()
            })
    return samples

samples = load_samples()

st.title("🔍 OCR Cleaning Test Viewer (10 Samples)")
st.markdown("Review the before/after results of the new prompt.")

for i, sample in enumerate(samples):
    st.markdown(f"### {sample['title']}")
    col1, col2 = st.columns(2)
    with col1:
        st.error("**Original (Corrupted OCR):**")
        st.write(sample['original'])
    with col2:
        st.success("**Cleaned (New Prompt):**")
        st.write(sample['cleaned'])
    st.markdown("---")

st.info("If these look good, tell the agent to run the batch job on the entire dataset!")
