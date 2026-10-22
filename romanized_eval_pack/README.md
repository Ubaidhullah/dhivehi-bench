# Dhivehi-Bench: Romanized Transliteration Human Evaluation (50 Items)

This package contains the interactive evaluation tool for Section 5.7 (Romanized Malé Latin Transliteration).

## How to Complete the Evaluation

1. **Open `index.html`** in any modern web browser (Google Chrome, Apple Safari, Microsoft Edge, or Mozilla Firefox).
   - No installation, internet server, or Python required.
2. **Enter your name** (e.g. `Hussein Arif` or `Hawwa La'aaly`).
3. For each of the 50 items:
   - Read the **English Source** and **Gold Reference**.
   - Inspect the **Model Output** (candidate translation in Romanized Dhivehi).
   - Click the **primary category** that best describes the translation:
     - 🔁 **1. Repetition Loop** (*ލަފުޒު / ފަސްއަކުރު ތަކުރާރުވުން*)
     - 🔤 **2. English Code-Switching** (*އިނގިރޭސި ލަފުޒަށް ދިވެހި ފަސްއަކުރު ގުޅުވުން*)
     - ❓ **3. Incoherent / Hallucination** (*މާނަ ދޭހަނުވާ / ބޭކާރު ބަސް*)
     - 📖 **4. Synonym / Register Variation** (*މާނަ ރަނގަޅު / އެހެން ލަފުޒެއް ނުވަތަ ޢާއްމު ބަސް*)
     - ✅ **5. Fluent & Accurate Translation** (*ރަނގަޅު ފުރިހަމަ ތަރުޖަމާ*)
4. Once you reach 50/50, click the green **"💾 Download JSON"** button in the top right.
5. Send the downloaded `.json` file back to the study team.

*Note: Your progress is automatically saved to your browser after every click.*
