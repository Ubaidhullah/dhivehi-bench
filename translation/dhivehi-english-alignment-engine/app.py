import streamlit as st
import os
import json
from dotenv import load_dotenv
from align import align_text

# Load environment variables
load_dotenv()
load_dotenv(".env.local")

st.set_page_config(page_title="Dhivehi-English Bitext Miner", layout="wide")

if "results" not in st.session_state:
    st.session_state.results = None

st.title("Dhivehi-English Alignment Engine")
st.markdown("Extract semantically equivalent sentence pairs from comparable documents.")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    api_key_env = os.getenv("API_KEY")
    api_key = st.text_input("Gemini API Key", value=api_key_env if api_key_env else "", type="password")
    if not api_key:
        st.warning("Please provide a Gemini API Key either here or in a .env file.")

    st.subheader("Metadata")
    source = st.text_input("Source", value="sun_media", help="e.g., sun_media, mihaaru")
    domain = st.text_input("Domain", value="news", help="e.g., news, legal, history")
    id_start = st.number_input("Start ID", min_value=1, value=1, step=1)

# Main Input Area
col1, col2 = st.columns(2)

# CSS for RTL support in the Dhivehi text area
st.markdown("""
    <style>
    /* Target the second text area for RTL */
    div[data-testid="stVerticalBlock"] > div:nth-child(2) textarea {
        direction: rtl;
    }
    .stAlert {
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

with col1:
    st.subheader("English Text (EN_TEXT)")
    english_text = st.text_area(
        "Paste English article here...", 
        height=400,
        placeholder="The Maldivian parliament, known as the Majlis..."
    )

with col2:
    st.subheader("Dhivehi Text (DV_TEXT)")
    dhivehi_text = st.text_area(
        "Paste Dhivehi article here...", 
        height=400,
        placeholder="...މިތަނަށް ދިވެހި އާޓިކަލް ކޮޕީކޮށްލައްވާ"
    )

# Action Button
if st.button("Start Mining", type="primary", disabled=not (english_text and dhivehi_text and api_key)):
    with st.spinner("Mining bitext pairs with Gemini..."):
        try:
            results = align_text(api_key, id_start, source, domain, english_text, dhivehi_text)
            st.session_state.results = results
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Results Display
if st.session_state.results:
    results = st.session_state.results
    st.divider()
    
    st.success(f"Successfully extracted {len(results)} pairs!")
    st.warning("⚠️  **MANUAL VERIFICATION REQUIRED:** AI models can hallucinate or misinterpret context. Please review the pairs below before saving.")

    # Helper functions for state management
    def delete_pair(index):
        if 0 <= index < len(st.session_state.results):
            del st.session_state.results[index]

    def update_pair(index, lang):
        # Callback to sync widget state to results list
        key = f"{lang}_{index}"
        if key in st.session_state:
            new_value = st.session_state[key]
            st.session_state.results[index]['translation'][lang] = new_value

    tab1, tab2, tab3 = st.tabs(["📝 Interactive Editor", "📋 Pretty JSON", "📄 Raw JSONL"])

    with tab1:
        # CSS to target textareas with specific aria-labels for RTL
        st.markdown("""
            <style>
            textarea[aria-label^="Dhivehi Content"] {
                direction: rtl;
                font-family: 'Faruma', 'MV Boli', sans-serif;
            }
            </style>
        """, unsafe_allow_html=True)

        # Iterate safely with index
        # We use a copy of the list for enumeration to avoid issues if items are deleted during iteration (though rerun handles this)
        for i, item in enumerate(st.session_state.results):
            with st.container():
                col_id, col_en, col_dv, col_action = st.columns([1, 4, 4, 1])
                
                with col_id:
                    st.caption(f"ID: {item['id']}")
                
                with col_en:
                    st.text_area(
                        "English Content",
                        value=item['translation']['en'],
                        key=f"en_{i}",
                        height=100,
                        label_visibility="collapsed",
                        on_change=update_pair,
                        args=(i, 'en') 
                    )

                with col_dv:
                    st.text_area(
                        "Dhivehi Content",
                        value=item['translation']['dv'],
                        key=f"dv_{i}",
                        height=100,
                        label_visibility="collapsed",
                        help="Dhivehi Text", # Adds aria-label usually
                        on_change=update_pair,
                        args=(i, 'dv')
                    )

                with col_action:
                    if st.button("🗑️", key=f"del_{i}", help="Remove this pair"):
                        delete_pair(i)
                        st.rerun()

            st.divider()

    with tab2:
        st.json(results, expanded=False)

    with tab3:
        jsonl_output = "\n".join([json.dumps(record, ensure_ascii=False) for record in results])
        st.text_area("Copy Raw Data", value=jsonl_output, height=300)

    # Save to File Section
    st.markdown("### 💾 Save Data")
    
    save_col1, save_col2 = st.columns([3, 1])
    
    with save_col1:
        file_path = st.text_input("Output Filename", value="aligned_corpus.jsonl", help="File will be created or appended to in the current directory.")
    
    with save_col2:
        # Spacer to align button
        st.write("") 
        st.write("")
        if st.button("Append to File", type="secondary"):
            if not file_path:
                st.error("Please specify a filename.")
            else:
                try:
                    jsonl_string = "\n".join([json.dumps(record, ensure_ascii=False) for record in results])
                    with open(file_path, "a", encoding="utf-8") as f:
                        f.write(jsonl_string + "\n")
                    st.toast(f"✅ Appended {len(results)} lines to {file_path}", icon="💾")
                except Exception as e:
                    st.error(f"Failed to save file: {e}")

elif not api_key:
    st.info("Please enter your API Key to enable the 'Start Mining' button.")
elif not (english_text and dhivehi_text):
    st.info("Please enter text in both English and Dhivehi fields to start.")
