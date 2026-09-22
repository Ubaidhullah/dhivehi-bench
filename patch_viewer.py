import re

with open("context_qa_viewer.py", "r") as f:
    content = f.read()

# Add the column if it doesn't exist
patch = """
df = pd.DataFrame(data)
if "status" not in df.columns:
    df["status"] = "pending"

# Status Filter
"""

content = content.replace("df = pd.DataFrame(data)\n\n# Status Filter\n", patch)

with open("context_qa_viewer.py", "w") as f:
    f.write(content)
