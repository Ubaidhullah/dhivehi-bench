import json
import os
import random
import argparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_PATH = os.path.join(BASE_DIR, "results", "romanized_ablation_200.json")
PACK_DIR = os.path.join(BASE_DIR, "romanized_eval_pack")
os.makedirs(PACK_DIR, exist_ok=True)


def load_stratified_items(total_target=50, seed=42):
    with open(RESULTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data["items"]
    rng = random.Random(seed)

    # Group items by domain
    by_dom = {"legal": [], "news": [], "speech": []}
    for idx, it in enumerate(items):
        d = it.get("domain", "speech")
        if d not in ("legal", "news", "speech"):
            d = "speech"
        by_dom[d].append((idx, it))

    for d in by_dom:
        rng.shuffle(by_dom[d])

    # Allocation proportional to target
    if total_target == 50:
        target_alloc = [
            ("legal", [("Gemma 4 (31B)", "gemma4", 6), ("Llama 3.1 (70B)", "llama70b", 5), ("Qwen 2.5 (72B)", "qwen72b", 4)]),
            ("news", [("Gemma 4 (31B)", "gemma4", 10), ("Llama 3.1 (70B)", "llama70b", 8), ("Qwen 2.5 (72B)", "qwen72b", 7)]),
            ("speech", [("Gemma 4 (31B)", "gemma4", 4), ("Llama 3.1 (70B)", "llama70b", 3), ("Qwen 2.5 (72B)", "qwen72b", 3)])
        ]
    else:  # 100 items
        target_alloc = [
            ("legal", [("Gemma 4 (31B)", "gemma4", 12), ("Llama 3.1 (70B)", "llama70b", 10), ("Qwen 2.5 (72B)", "qwen72b", 8)]),
            ("news", [("Gemma 4 (31B)", "gemma4", 17), ("Llama 3.1 (70B)", "llama70b", 17), ("Qwen 2.5 (72B)", "qwen72b", 16)]),
            ("speech", [("Gemma 4 (31B)", "gemma4", 5), ("Llama 3.1 (70B)", "llama70b", 6), ("Qwen 2.5 (72B)", "qwen72b", 9)])
        ]

    selected = []
    item_cursor = {"legal": 0, "news": 0, "speech": 0}

    for dom, model_counts in target_alloc:
        for model_label, model_key, count in model_counts:
            for _ in range(count):
                idx, it = by_dom[dom][item_cursor[dom]]
                item_cursor[dom] += 1
                pred = it["predictions"][model_key]["romanized"]
                selected.append({
                    "source_idx": idx,
                    "item_id": it["id"],
                    "domain": dom,
                    "model_label": model_label,
                    "model_key": model_key,
                    "english": it["english"],
                    "gold_romanized": it["gold_romanized"],
                    "gold_thaana": it["gold_thaana"],
                    "prediction": pred
                })

    rng.shuffle(selected)

    final_items = []
    for num, it in enumerate(selected, start=1):
        final_items.append({
            "id": f"rom_{num:03d}",
            "num": num,
            "domain": it["domain"],
            "model_key": it["model_key"],
            "model_label": it["model_label"],
            "source_idx": it["source_idx"],
            "english": it["english"],
            "gold_romanized": it["gold_romanized"],
            "gold_thaana": it["gold_thaana"],
            "prediction": it["prediction"]
        })

    return final_items


def build_html(items):
    items_json = json.dumps(items, ensure_ascii=False, indent=2)
    n_items = len(items)

    return f"""<!DOCTYPE html>
<html lang="dv" dir="ltr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dhivehi-Bench: Romanized Dhivehi Human Evaluation (n = {n_items})</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    :root {{
      --thaana-font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Faruma", "MV Boli", "Noto Sans Thaana", sans-serif;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: #0b1120;
      color: #f1f5f9;
    }}
    .thaana-text {{
      font-family: var(--thaana-font);
      direction: rtl;
      text-align: right;
      line-height: 2.1;
      font-size: 1.15rem;
    }}
  </style>
</head>
<body class="min-h-screen flex flex-col selection:bg-indigo-500 selection:text-white">

  <!-- Sticky Top Bar -->
  <header class="bg-slate-900/95 backdrop-blur border-b border-slate-800 sticky top-0 z-30 shadow-lg">
    <div class="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between gap-4 flex-wrap">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center font-bold text-white shadow-lg text-lg">
          L
        </div>
        <div>
          <h1 class="text-base font-bold text-white">Dhivehi-Bench: Romanized Transliteration Audit (n = {n_items})</h1>
          <p class="text-xs text-slate-400">Section 5.7 Qualitative Categorization &amp; Inter-Annotator Agreement</p>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2 bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800 text-xs">
          <span class="text-slate-400">Annotator:</span>
          <span id="display-name" class="font-semibold text-sky-400">Not Set</span>
          <button onclick="promptName()" class="text-[11px] text-slate-500 hover:text-slate-300 ml-1">✏️</button>
        </div>
        <div class="text-xs font-mono bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800">
          <span class="text-slate-400">Coded:</span>
          <span id="progress-badge" class="text-sky-400 font-bold ml-1">0 / {n_items}</span>
        </div>
        <button onclick="downloadResults()" class="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md transition flex items-center gap-1.5">
          <span>💾</span>
          <span>Download JSON</span>
        </button>
      </div>
    </div>
  </header>

  <main class="flex-1 max-w-5xl w-full mx-auto px-4 py-6">
    <!-- Coding Rubric Banner -->
    <div class="bg-slate-900 rounded-2xl border border-slate-800 p-5 mb-6 shadow-md">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-xs font-bold uppercase tracking-wider text-sky-400">
          📋 Coding Guidelines &amp; Priority Hierarchy (ކޮންމެ ތަރުޖަމާއަކަށް 1 ކެޓަގަރީ ހޮއްވަވާ)
        </h2>
        <span class="text-[11px] bg-slate-800 px-2 py-0.5 rounded text-slate-400 font-mono">1 to 5 keys supported</span>
      </div>
      <p class="text-xs text-slate-300 mb-3 leading-relaxed">
        އެންމެ އިސްކަންދޭންވީ އުސޫލު (If an output shows multiple issues, apply this priority hierarchy from 1 to 5):
      </p>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5 text-xs">
        <div class="bg-slate-950/80 border border-amber-900/40 rounded-xl p-3">
          <div class="font-bold text-amber-400 flex items-center gap-1.5">
            <span>🔁</span> 1. Morphological / Repetition Loop
          </div>
          <div class="text-slate-200 mt-1 font-medium thaana-text text-[13px] leading-snug">ލަފުޒު / ފަސްއަކުރު ތަކުރާރުވުން</div>
          <div class="text-slate-400 mt-1 text-[11px]">Repeating words, suffixes, or particles 3+ times (e.g. <em>thah thah thah</em>, <em>kuraa kuraa</em>, <em>fali-fali</em>).</div>
        </div>

        <div class="bg-slate-950/80 border border-indigo-900/40 rounded-xl p-3">
          <div class="font-bold text-indigo-400 flex items-center gap-1.5">
            <span>🔤</span> 2. English Code-Switching
          </div>
          <div class="text-slate-200 mt-1 font-medium thaana-text text-[13px] leading-snug">އިނގިރޭސި ލަފުޒަށް ދިވެހި ފަސްއަކުރު ގުޅުވުން</div>
          <div class="text-slate-400 mt-1 text-[11px]">Keeping English nouns/stems with Dhivehi suffixes (e.g. <em>members-ah</em>, <em>court-ge</em>, <em>disability thah</em>).</div>
        </div>

        <div class="bg-slate-950/80 border border-rose-900/40 rounded-xl p-3">
          <div class="font-bold text-rose-400 flex items-center gap-1.5">
            <span>❓</span> 3. Incoherent / Hallucination
          </div>
          <div class="text-slate-200 mt-1 font-medium thaana-text text-[13px] leading-snug">މާނަ ދޭހަނުވާ / ބޭކާރު ބަސް</div>
          <div class="text-slate-400 mt-1 text-[11px]">Severe hallucination, broken meaningless Latin roots, gibberish, or completely unrelated meaning.</div>
        </div>

        <div class="bg-slate-950/80 border border-emerald-900/40 rounded-xl p-3">
          <div class="font-bold text-emerald-400 flex items-center gap-1.5">
            <span>📖</span> 4. Synonym / Register Variation
          </div>
          <div class="text-slate-200 mt-1 font-medium thaana-text text-[13px] leading-snug">މާނަ ރަނގަޅު / އެހެން ލަފުޒެއް ނުވަތަ ޢާއްމު ބަސް</div>
          <div class="text-slate-400 mt-1 text-[11px]">Understood &amp; correct Dhivehi meaning, but uses everyday/alternative synonyms differing from formal reference.</div>
        </div>

        <div class="bg-slate-950/80 border border-sky-900/40 rounded-xl p-3 md:col-span-2 lg:col-span-2">
          <div class="font-bold text-sky-400 flex items-center gap-1.5">
            <span>✅</span> 5. Fluent &amp; Accurate Translation
          </div>
          <div class="text-slate-200 mt-1 font-medium thaana-text text-[13px] leading-snug">ރަނގަޅު ފުރިހަމަ ތަރުޖަމާ</div>
          <div class="text-slate-400 mt-1 text-[11px]">Natural, fluent, and accurate Dhivehi translation in Latin script with no major flaws.</div>
        </div>
      </div>
    </div>

    <!-- Filter Bar -->
    <div class="flex items-center justify-between mb-4 text-xs">
      <div class="flex items-center gap-2">
        <button onclick="setFilter('all')" id="filter-all" class="px-3 py-1 rounded-lg bg-sky-600 text-white font-semibold">Show All ({n_items})</button>
        <button onclick="setFilter('uncoded')" id="filter-uncoded" class="px-3 py-1 rounded-lg bg-slate-900 text-slate-400 hover:bg-slate-800">Uncoded Only</button>
      </div>
      <div id="live-breakdown" class="text-slate-400 font-mono text-[11px]"></div>
    </div>

    <div id="items-container" class="flex flex-col gap-5"></div>
  </main>

  <script>
    const ITEMS = {items_json};
    const STORAGE_KEY = "dhivehi_bench_romanized_eval_v1";
    const NAME_KEY = "dhivehi_bench_romanized_eval_name";

    const CATEGORIES = [
      {{ key: "particle_loops", num: "1", icon: "🔁", label: "1. Repetition Loop", dv: "ލަފުޒު / ފަސްއަކުރު ތަކުރާރުވުން", color: "amber" }},
      {{ key: "code_switching", num: "2", icon: "🔤", label: "2. English Code-Switching", dv: "އިނގިރޭސި ލަފުޒަށް ދިވެހި ފަސްއަކުރު ގުޅުވުން", color: "indigo" }},
      {{ key: "incoherent_hallucination", num: "3", icon: "❓", label: "3. Incoherent / Hallucination", dv: "މާނަ ދޭހަނުވާ / ބޭކާރު ބަސް", color: "rose" }},
      {{ key: "synonymy_register", num: "4", icon: "📖", label: "4. Synonym / Register Variation", dv: "މާނަ ރަނގަޅު / އެހެން ލަފުޒެއް", color: "emerald" }},
      {{ key: "fluent_translation", num: "5", icon: "✅", label: "5. Fluent & Accurate", dv: "ރަނގަޅު ފުރިހަމަ ތަރުޖަމާ", color: "sky" }}
    ];

    let state = {{}};
    let currentFilter = "all";

    function loadState() {{
      try {{
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) state = JSON.parse(saved);
      }} catch (e) {{
        console.error(e);
      }}
      const savedName = localStorage.getItem(NAME_KEY);
      if (savedName) {{
        document.getElementById("display-name").textContent = savedName;
      }} else {{
        setTimeout(promptName, 300);
      }}
    }}

    function promptName() {{
      const current = localStorage.getItem(NAME_KEY) || "";
      const name = prompt("Enter your name (e.g. Hussein Arif or Hawwa La'aaly):", current);
      if (name && name.trim()) {{
        localStorage.setItem(NAME_KEY, name.trim());
        document.getElementById("display-name").textContent = name.trim();
      }}
    }}

    function selectCategory(itemId, catKey) {{
      state[itemId] = catKey;
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      updateCardUI(itemId);
      updateHeaderStats();
    }}

    function setFilter(mode) {{
      currentFilter = mode;
      document.getElementById("filter-all").className = mode === "all"
        ? "px-3 py-1 rounded-lg bg-sky-600 text-white font-semibold"
        : "px-3 py-1 rounded-lg bg-slate-900 text-slate-400 hover:bg-slate-800";
      document.getElementById("filter-uncoded").className = mode === "uncoded"
        ? "px-3 py-1 rounded-lg bg-sky-600 text-white font-semibold"
        : "px-3 py-1 rounded-lg bg-slate-900 text-slate-400 hover:bg-slate-800";
      renderAll();
    }}

    function updateHeaderStats() {{
      const codedCount = Object.keys(state).length;
      const total = ITEMS.length;
      document.getElementById("progress-badge").textContent = `${{codedCount}} / ${{total}}`;
      if (codedCount === total) {{
        document.getElementById("progress-badge").className = "text-emerald-400 font-bold ml-1";
      }} else {{
        document.getElementById("progress-badge").className = "text-sky-400 font-bold ml-1";
      }}

      // Tally categories
      const counts = {{}};
      CATEGORIES.forEach(c => counts[c.key] = 0);
      Object.values(state).forEach(k => {{
        if (counts[k] !== undefined) counts[k]++;
      }});
      const parts = CATEGORIES.map(c => `${{c.icon}} ${{counts[c.key]}}`);
      document.getElementById("live-breakdown").textContent = parts.join(" | ");
    }}

    function toggleThaana(itemId) {{
      const el = document.getElementById(`thaana-${{itemId}}`);
      if (el) {{
        el.classList.toggle("hidden");
      }}
    }}

    function renderCard(item) {{
      const currentCat = state[item.id];
      const isCoded = !!currentCat;

      const buttonsHtml = CATEGORIES.map(c => {{
        const isSelected = currentCat === c.key;
        let btnClasses = "";
        if (isSelected) {{
          if (c.color === "amber") btnClasses = "bg-amber-600 border-amber-400 text-white shadow-lg ring-2 ring-amber-400/50";
          else if (c.color === "indigo") btnClasses = "bg-indigo-600 border-indigo-400 text-white shadow-lg ring-2 ring-indigo-400/50";
          else if (c.color === "rose") btnClasses = "bg-rose-600 border-rose-400 text-white shadow-lg ring-2 ring-rose-400/50";
          else if (c.color === "emerald") btnClasses = "bg-emerald-600 border-emerald-400 text-white shadow-lg ring-2 ring-emerald-400/50";
          else if (c.color === "sky") btnClasses = "bg-sky-600 border-sky-400 text-white shadow-lg ring-2 ring-sky-400/50";
        }} else {{
          btnClasses = "bg-slate-900 hover:bg-slate-800 border-slate-800 text-slate-300";
        }}

        return `
          <button onclick="selectCategory('${{item.id}}', '${{c.key}}')"
                  class="flex flex-col text-left p-2.5 rounded-xl border transition-all text-xs ${{btnClasses}} group">
            <div class="flex items-center justify-between w-full">
              <span class="font-bold flex items-center gap-1.5">
                <span>${{c.icon}}</span>
                <span>${{c.label}}</span>
              </span>
              <span class="text-[10px] opacity-60 font-mono px-1 rounded bg-black/30">[${{c.num}}]</span>
            </div>
            <div class="thaana-text text-[12px] opacity-90 mt-1 leading-tight">${{c.dv}}</div>
          </button>
        `;
      }}).join("");

      return `
        <div id="card-${{item.id}}" class="bg-slate-900/90 rounded-2xl border ${{isCoded ? 'border-sky-800/60' : 'border-slate-800'}} p-5 shadow-lg transition-all">
          <div class="flex items-center justify-between border-b border-slate-800 pb-2.5 mb-3.5">
            <div class="flex items-center gap-2">
              <span class="px-2 py-0.5 rounded bg-sky-950 border border-sky-800 text-sky-400 text-xs font-bold font-mono">#${{item.num}}</span>
              <span class="text-xs text-slate-400 font-mono capitalize">Domain: ${{item.domain}}</span>
              <span class="text-[11px] text-slate-500 font-mono">ID: ${{item.id}}</span>
            </div>
            <div class="flex items-center gap-2">
              <button onclick="toggleThaana('${{item.id}}')" class="text-[11px] text-slate-400 hover:text-sky-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800 transition">
                👁️ Toggle Thaana Script
              </button>
              ${{isCoded ? '<span class="text-[11px] text-emerald-400 font-semibold flex items-center gap-1"><span>✓</span> Coded</span>' : '<span class="text-[11px] text-slate-500">Uncoded</span>'}}
            </div>
          </div>

          <!-- English Source -->
          <div class="mb-3">
            <div class="text-[11px] uppercase font-bold text-slate-400 tracking-wider mb-1">Source (English)</div>
            <div class="text-sm text-slate-200 bg-slate-950/70 p-3 rounded-xl border border-slate-800/80 leading-relaxed font-sans">
              ${{item.english}}
            </div>
          </div>

          <!-- Gold Reference -->
          <div class="mb-3">
            <div class="text-[11px] uppercase font-bold text-emerald-400 tracking-wider mb-1">Gold Reference (Official Malé Latin)</div>
            <div class="text-sm text-emerald-200/95 bg-emerald-950/20 p-3 rounded-xl border border-emerald-900/40 leading-relaxed font-mono text-[13px]">
              ${{item.gold_romanized}}
            </div>
            <div id="thaana-${{item.id}}" class="hidden mt-1.5 p-2.5 rounded-xl bg-slate-950/90 border border-slate-800 text-amber-200 thaana-text text-sm">
              ${{item.gold_thaana}}
            </div>
          </div>

          <!-- Model Prediction -->
          <div class="mb-4">
            <div class="text-[11px] uppercase font-bold text-sky-400 tracking-wider mb-1">Model Output (Romanized Candidate)</div>
            <div class="text-sm text-sky-200 bg-sky-950/20 p-3.5 rounded-xl border border-sky-800/40 leading-relaxed font-mono text-[13px] break-words">
              ${{item.prediction}}
            </div>
          </div>

          <!-- Coding Buttons -->
          <div>
            <div class="text-[11px] uppercase font-bold text-slate-400 tracking-wider mb-2">Select Primary Category:</div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
              ${{buttonsHtml}}
            </div>
          </div>
        </div>
      `;
    }}

    function updateCardUI(itemId) {{
      const item = ITEMS.find(x => x.id === itemId);
      if (!item) return;
      const cardEl = document.getElementById(`card-${{itemId}}`);
      if (cardEl) {{
        cardEl.outerHTML = renderCard(item);
      }}
    }}

    function renderAll() {{
      const container = document.getElementById("items-container");
      const filtered = ITEMS.filter(item => {{
        if (currentFilter === "uncoded") return !state[item.id];
        return true;
      }});

      if (filtered.length === 0) {{
        container.innerHTML = `
          <div class="text-center py-16 bg-slate-900 rounded-2xl border border-slate-800">
            <div class="text-4xl mb-3">🎉</div>
            <h3 class="text-base font-bold text-white mb-1">All Items Coded!</h3>
            <p class="text-xs text-slate-400 mb-4">Click "Download JSON" at the top to save and return your ratings.</p>
            <button onclick="setFilter('all')" class="px-4 py-2 rounded-xl bg-sky-600 text-white text-xs font-semibold">Review All Items</button>
          </div>
        `;
        return;
      }}

      container.innerHTML = filtered.map(renderCard).join("");
      updateHeaderStats();
    }}

    function downloadResults() {{
      const name = localStorage.getItem(NAME_KEY) || "annotator";
      const codedCount = Object.keys(state).length;
      const total = ITEMS.length;

      if (codedCount < total) {{
        const proceed = confirm(`You have coded ${{codedCount}} of ${{total}} items. Do you want to download now anyway?`);
        if (!proceed) return;
      }}

      const payload = {{
        annotator: name,
        timestamp: new Date().toISOString(),
        total_items: total,
        coded_items: codedCount,
        ratings: state,
        metadata: ITEMS.map(it => ({{
          id: it.id,
          num: it.num,
          domain: it.domain,
          model_key: it.model_key,
          model_label: it.model_label,
          coded_category: state[it.id] || null
        }}))
      }};

      const blob = new Blob([JSON.stringify(payload, null, 2)], {{ type: "application/json" }});
      const url = URL.createObjectURL(blob);
      const sanitizedName = name.toLowerCase().replace(/[^a-z0-9]/g, "_");
      const a = document.createElement("a");
      a.href = url;
      a.download = `romanized_eval_${{sanitizedName}}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }}

    window.addEventListener("DOMContentLoaded", () => {{
      loadState();
      renderAll();
    }});
  </script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Generate Romanized Human Evaluation Pack")
    parser.add_argument("--count", type=int, default=50, choices=[50, 100], help="Number of items to sample")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    items = load_stratified_items(total_target=args.count, seed=args.seed)

    # Save raw JSON items
    items_path = os.path.join(PACK_DIR, f"romanized_items_{args.count}.json")
    with open(items_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    # Generate index.html
    html_content = build_html(items)
    html_path = os.path.join(PACK_DIR, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Generate README.md
    readme_content = f"""# Dhivehi-Bench: Romanized Transliteration Human Evaluation ({args.count} Items)

This package contains the interactive evaluation tool for Section 5.7 (Romanized Malé Latin Transliteration).

## How to Complete the Evaluation

1. **Open `index.html`** in any modern web browser (Google Chrome, Apple Safari, Microsoft Edge, or Mozilla Firefox).
   - No installation, internet server, or Python required.
2. **Enter your name** (e.g. `Hussein Arif` or `Hawwa La'aaly`).
3. For each of the {args.count} items:
   - Read the **English Source** and **Gold Reference**.
   - Inspect the **Model Output** (candidate translation in Romanized Dhivehi).
   - Click the **primary category** that best describes the translation:
     - 🔁 **1. Repetition Loop** (*ލަފުޒު / ފަސްއަކުރު ތަކުރާރުވުން*)
     - 🔤 **2. English Code-Switching** (*އިނގިރޭސި ލަފުޒަށް ދިވެހި ފަސްއަކުރު ގުޅުވުން*)
     - ❓ **3. Incoherent / Hallucination** (*މާނަ ދޭހަނުވާ / ބޭކާރު ބަސް*)
     - 📖 **4. Synonym / Register Variation** (*މާނަ ރަނގަޅު / އެހެން ލަފުޒެއް ނުވަތަ ޢާއްމު ބަސް*)
     - ✅ **5. Fluent & Accurate Translation** (*ރަނގަޅު ފުރިހަމަ ތަރުޖަމާ*)
4. Once you reach {args.count}/{args.count}, click the green **"💾 Download JSON"** button in the top right.
5. Send the downloaded `.json` file back to the study team.

*Note: Your progress is automatically saved to your browser after every click.*
"""
    with open(os.path.join(PACK_DIR, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)

    print(f"Successfully generated {args.count} items in {PACK_DIR}")
    print(f"  - {items_path}")
    print(f"  - {html_path}")
    print(f"  - {os.path.join(PACK_DIR, 'README.md')}")


if __name__ == "__main__":
    main()
