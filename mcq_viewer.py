import streamlit as st
import json
import pandas as pd
import os

st.set_page_config(page_title="Dhivehi MCQ Curator", layout="wide")
DATA_FILE = "mcq/data/mcq_dataset_categorized.jsonl"

def load_data():
    data = []
    if not os.path.exists(DATA_FILE): return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            try:
                row = json.loads(line)
                if 'id' not in row:
                    row['id'] = str(i) # give them unique IDs if missing
                data.append(row)
            except json.JSONDecodeError:
                continue
    return data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        for row in data:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

st.title("🛠️ Dhivehi MCQ Curator")
st.markdown("Manually review, edit, or delete MCQs. Mark them as confirmed when done!")

data = load_data()
if not data:
    st.warning("No data found!")
    st.stop()

# Count categories
cat_counts = pd.Series([d.get('category', 'Unknown') for d in data]).value_counts()
confirmed_count = sum(1 for d in data if d.get('status') == 'confirmed')

st.sidebar.header("Dataset Stats")
st.sidebar.markdown(f"**Total MCQs:** {len(data)}")
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

items_per_page = 5
total_pages = max(1, (len(df) - 1) // items_per_page + 1)
page = st.sidebar.number_input("Page", min_value=1, max_value=total_pages, value=1)

start_idx = (page - 1) * items_per_page
end_idx = start_idx + items_per_page
page_data = df.iloc[start_idx:end_idx]

for i, row in page_data.iterrows():
    q_id = row['id']
    is_confirmed = row.get('status') == 'confirmed'
    
    with st.container():
        st.markdown("---")
        header_color = "🟢 CONFIRMED" if is_confirmed else "🟡 PENDING"
        st.markdown(f"### {header_color} | **Source:** `{row.get('source_file', 'Unknown')}` | **Category:** `{row.get('category', 'Unknown')}`")
        
        new_q = st.text_input("Question:", value=row['question'], key=f"q_{q_id}")
        
        # Options
        opts = row.get('options', [])
        new_opts = []
        col_opts1, col_opts2 = st.columns(2)
        for opt_idx, opt in enumerate(opts):
            # Split into column A/C and B/D layout
            col = col_opts1 if opt_idx % 2 == 0 else col_opts2
            with col:
                new_opts.append(st.text_input(f"Option {opt_idx+1}", value=opt, key=f"opt_{q_id}_{opt_idx}"))
                
        col_ans, col_exp = st.columns([2, 8])
        with col_ans:
            new_a = st.text_input("Answer (e.g. A):", value=row.get('answer', ''), key=f"a_{q_id}")
        with col_exp:
            new_exp = st.text_input("Explanation:", value=row.get('explanation', ''), key=f"exp_{q_id}")
            
        col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 8])
        with col_btn1:
            if st.button("🗑️ Delete MCQ", key=f"del_{q_id}"):
                data = [d for d in data if d.get('id') != q_id]
                save_data(data)
                st.rerun()
                
        with col_btn2:
            if not is_confirmed:
                if st.button("✅ Confirm MCQ", type="primary", key=f"confirm_{q_id}"):
                    for d in data:
                        if d.get('id') == q_id:
                            d['status'] = 'confirmed'
                            # Auto save edits if any
                            d['question'] = new_q
                            d['options'] = new_opts
                            d['answer'] = new_a
                            d['explanation'] = new_exp
                            break
                    save_data(data)
                    st.rerun()
            else:
                if st.button("❌ Un-confirm", key=f"unconfirm_{q_id}"):
                    for d in data:
                        if d.get('id') == q_id:
                            d['status'] = 'pending'
                            break
                    save_data(data)
                    st.rerun()
                    
        with col_btn3:
            # Check if any edits made
            if new_q != row['question'] or new_opts != opts or new_a != row.get('answer', '') or new_exp != row.get('explanation', ''):
                if st.button("💾 Save Edits", key=f"save_{q_id}"):
                    for d in data:
                        if d.get('id') == q_id:
                            d['question'] = new_q
                            d['options'] = new_opts
                            d['answer'] = new_a
                            d['explanation'] = new_exp
                            break
                    save_data(data)
                    st.success("MCQ updated!")
                    st.rerun()
