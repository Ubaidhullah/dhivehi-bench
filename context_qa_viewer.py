import streamlit as st
import json
import pandas as pd
import os

st.set_page_config(page_title="Dhivehi SQuAD Curator", layout="wide")
DATA_FILE = "context_qa/data/context_qa_dataset_polished_v2.jsonl"

def load_data():
    data = []
    if not os.path.exists(DATA_FILE): return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        for row in data:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

st.title("🛠️ Dhivehi Contextual QA Curator")
st.markdown("Manually review, edit, or delete paragraphs and QA pairs. Mark them as confirmed when done!")

data = load_data()
if not data:
    st.warning("No data found!")
    st.stop()

# Count categories
cat_counts = pd.Series([d.get('category', 'Unknown') for d in data]).value_counts()
confirmed_count = sum(1 for d in data if d.get('status') == 'confirmed')

st.sidebar.header("Dataset Stats")
st.sidebar.markdown(f"**Total QA Pairs:** {len(data)}")
st.sidebar.markdown(f"✅ **Confirmed:** {confirmed_count} / {len(data)}")
st.sidebar.markdown("---")
for cat, count in cat_counts.items():
    st.sidebar.markdown(f"- **{cat}**: {count}")

st.sidebar.header("Filters")

df = pd.DataFrame(data)
if "status" not in df.columns:
    df["status"] = "pending"

# Status Filter
status_filter = st.sidebar.radio("Show Status", ["Pending Review", "Confirmed", "All"])
if status_filter == "Pending Review":
    df = df[df["status"] != "confirmed"]
elif status_filter == "Confirmed":
    df = df[df["status"] == "confirmed"]

if df.empty:
    st.success("No items match your filter! Great job!")
    st.stop()

categories = ["All"] + sorted(df["category"].dropna().unique().tolist())
selected_category = st.sidebar.selectbox("Filter by Category", categories)

if selected_category != "All":
    df = df[df["category"] == selected_category]

if df.empty:
    st.warning("No items match this category filter.")
    st.stop()

items_per_page = 2
unique_contexts = df["context"].unique()
total_pages = max(1, (len(unique_contexts) - 1) // items_per_page + 1)
page = st.sidebar.number_input("Page", min_value=1, max_value=total_pages, value=1)

start_idx = (page - 1) * items_per_page
end_idx = start_idx + items_per_page
page_contexts = unique_contexts[start_idx:end_idx]

for ctx_idx, context in enumerate(page_contexts):
    context_df = df[df["context"] == context]
    first_row = context_df.iloc[0]
    
    # Check if all rows for this context are confirmed
    is_confirmed = all(r.get('status') == 'confirmed' for _, r in context_df.iterrows())
    
    with st.container():
        st.markdown("---")
        header_color = "🟢 CONFIRMED" if is_confirmed else "🟡 PENDING"
        st.markdown(f"### {header_color} | **Source:** `{first_row['source_file']}` | **Category:** `{first_row.get('category', 'Unknown')}`")
        
        # Edit Paragraph
        new_context = st.text_area("Paragraph (Context):", value=context, height=150, key=f"ctx_{ctx_idx}_{page}")
        
        col_ctx_1, col_ctx_2, col_ctx_3 = st.columns([2, 2, 8])
        with col_ctx_1:
            if st.button("🗑️ Delete Entire Paragraph", key=f"del_ctx_{ctx_idx}_{page}"):
                data = [d for d in data if d['context'] != context]
                save_data(data)
                st.rerun()
        with col_ctx_2:
            if not is_confirmed:
                if st.button("✅ Confirm Paragraph & QA", type="primary", key=f"confirm_ctx_{ctx_idx}_{page}"):
                    for d in data:
                        if d['context'] == context:
                            d['status'] = 'confirmed'
                            d['context'] = new_context # Save edits too
                    save_data(data)
                    st.rerun()
            else:
                if st.button("❌ Un-confirm", key=f"unconfirm_ctx_{ctx_idx}_{page}"):
                    for d in data:
                        if d['context'] == context:
                            d['status'] = 'pending'
                    save_data(data)
                    st.rerun()
        
        with col_ctx_3:
            if new_context != context:
                if st.button("💾 Save Paragraph Edit", key=f"save_ctx_{ctx_idx}_{page}"):
                    for d in data:
                        if d['context'] == context:
                            d['context'] = new_context
                    save_data(data)
                    st.success("Paragraph updated!")
                    st.rerun()
        
        st.markdown("#### Questions:")
        for i, row in context_df.iterrows():
            q_id = row.get('id', str(i))
            with st.expander(f"Q: {row['question'][:60]}...", expanded=True):
                new_q = st.text_input("Question", value=row['question'], key=f"q_{q_id}")
                new_a = st.text_area("Answer", value=row['answer'], key=f"a_{q_id}")
                
                col1, col2 = st.columns([1, 10])
                with col1:
                    if st.button("🗑️ Delete Q", key=f"del_{q_id}"):
                        data = [d for d in data if d.get('id') != q_id]
                        save_data(data)
                        st.rerun()
                with col2:
                    if new_q != row['question'] or new_a != row['answer']:
                        if st.button("💾 Save Q/A Edits", key=f"save_{q_id}"):
                            for d in data:
                                if d.get('id') == q_id:
                                    d['question'] = new_q
                                    d['answer'] = new_a
                                    break
                            save_data(data)
                            st.success("Saved!")
                            st.rerun()
