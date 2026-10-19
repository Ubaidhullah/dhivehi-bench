import json
import os
import random
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
PACK_DIR = os.path.join(BASE_DIR, "error_coding_pack")
os.makedirs(PACK_DIR, exist_ok=True)


def has_repetition_loop(text: str) -> bool:
    if not text or len(text) < 40:
        return False
    words = text.split()
    if len(words) >= 12:
        for i in range(len(words) - 6):
            gram = " ".join(words[i : i + 2])
            if len(gram) >= 4 and text.count(gram) >= 4:
                return True
    for m in re.finditer(r"(.{4,25}?)\1{3,}", text):
        return True
    return False


def has_foreign_script(text: str) -> bool:
    if not text:
        return False
    # Check for Latin letters, Arabic script (U+0600-U+06FF), Indic/CJK scripts outside Thaana (U+0780-U+07BF)
    for ch in text:
        cp = ord(ch)
        if (0x0041 <= cp <= 0x005A) or (0x0061 <= cp <= 0x007A):
            return True
        if (0x0600 <= cp <= 0x06FF and cp not in (0x060C, 0x061B, 0x061F)):
            return True
        if (0x0900 <= cp <= 0x0DFF) or (0x4E00 <= cp <= 0x9FFF) or (0x0400 <= cp <= 0x04FF):
            return True
    return False


def load_candidates():
    models = [
        ("Gemma 4 (31B)", "translation_gemma4_full.json"),
        ("Llama 3.1 (70B)", "translation_llama70b.json"),
        ("Qwen 2.5 (72B)", "translation_qwen72b.json"),
    ]
    all_rows = []
    for model_name, filename in models:
        path = os.path.join(RESULTS_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for idx, item in enumerate(data):
            en = item.get("english", "").strip()
            target = item.get("target", "").strip()
            pred = item.get("prediction", "").strip()
            if not en or not target or not pred or pred == target:
                continue
            # Keep medium-length source sentences for fast, clear human inspection
            if 8 <= len(en.split()) <= 40:
                all_rows.append(
                    {
                        "source_idx": idx,
                        "model": model_name,
                        "english": en,
                        "target": target,
                        "prediction": pred,
                    }
                )
    return all_rows


def select_stratified_100(all_rows):
    rng = random.Random(42)
    rng.shuffle(all_rows)

    # Bucket candidates heuristically so the 100-item sample contains a natural variety
    # across all 3 models and all 4 failure modes without exposing labels to coders
    loops, scripts, morph_or_drift = [], [], []
    for r in all_rows:
        pred = r["prediction"]
        if has_repetition_loop(pred):
            loops.append(r)
        elif has_foreign_script(pred):
            scripts.append(r)
        else:
            morph_or_drift.append(r)

    selected = []
    used_keys = set()

    def take_from(bucket, count):
        taken = 0
        # Balance across models inside each bucket
        for model_name in ["Gemma 4 (31B)", "Llama 3.1 (70B)", "Qwen 2.5 (72B)"]:
            sub = [x for x in bucket if x["model"] == model_name]
            target_sub = count // 3 + (1 if taken < count % 3 else 0)
            c = 0
            for item in sub:
                key = (item["model"], item["source_idx"])
                if key not in used_keys and c < target_sub and len(selected) < 100:
                    used_keys.add(key)
                    selected.append(item)
                    c += 1
                    taken += 1

    take_from(morph_or_drift, 50)
    take_from(loops, 30)
    take_from(scripts, 20)

    # Fill any remaining slots up to 100
    for item in all_rows:
        if len(selected) >= 100:
            break
        key = (item["model"], item["source_idx"])
        if key not in used_keys:
            used_keys.add(key)
            selected.append(item)

    rng.shuffle(selected)
    final_items = []
    for i, item in enumerate(selected[:100], start=1):
        pred_display = item["prediction"]
        is_truncated = False
        if len(pred_display) > 550:
            pred_display = pred_display[:550] + " … [continues]"
            is_truncated = True
        final_items.append(
            {
                "id": f"err_{i:03d}",
                "number": i,
                "model": item["model"],
                "source_idx": item["source_idx"],
                "english": item["english"],
                "target": item["target"],
                "prediction": pred_display,
                "full_length_chars": len(item["prediction"]),
                "is_truncated": is_truncated,
            }
        )
    return final_items


def build_html(items):
    items_json = json.dumps(items, ensure_ascii=False, indent=2)
    return f"""<!DOCTYPE html>
<html lang="dv" dir="ltr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dhivehi-Bench Section 6.5 Error Morphology Coding (100 Items)</title>
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
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-rose-500 flex items-center justify-center font-bold text-white shadow-lg text-lg">
          ދ
        </div>
        <div>
          <h1 class="text-base font-bold text-white">Dhivehi-Bench: Error Morphology Coding (n = 100)</h1>
          <p class="text-xs text-slate-400">Section 6.5 Qualitative Error Taxonomy &amp; Cohen's κ Audit</p>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2 bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800 text-xs">
          <span class="text-slate-400">Annotator:</span>
          <span id="display-name" class="font-semibold text-indigo-400">Not Set</span>
          <button onclick="promptName()" class="text-[11px] text-slate-500 hover:text-slate-300 ml-1">✏️</button>
        </div>
        <div class="text-xs font-mono bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800">
          <span class="text-slate-400">Coded:</span>
          <span id="progress-badge" class="text-indigo-400 font-bold ml-1">0 / 100</span>
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
    <div class="bg-slate-900 rounded-2xl border border-slate-800 p-4 mb-6 shadow-md">
      <h2 class="text-xs font-bold uppercase tracking-wider text-indigo-400 mb-2">
        📋 Coding Guidelines (Pick the Primary Error Category for Each Output)
      </h2>
      <p class="text-xs text-slate-300 mb-3 leading-relaxed">
        To ensure consistent inter-annotator agreement, if a model output shows more than one issue, apply this priority rule from top (1) to bottom (4):
      </p>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-2.5 text-xs">
        <div class="bg-slate-950/80 border border-slate-800 rounded-xl p-2.5">
          <div class="font-bold text-amber-400">1. Repetition Loops (ތަކުރާރުވުން)</div>
          <div class="text-slate-400 mt-0.5">Check first: Does the output get stuck repeating the same word, phrase, or syllable 3+ times in a row?</div>
        </div>
        <div class="bg-slate-950/80 border border-slate-800 rounded-xl p-2.5">
          <div class="font-bold text-rose-400">2. Arabic / Latin Script Mixing (އަކުރު މަސްހުނިވުން)</div>
          <div class="text-slate-400 mt-0.5">If not looping: Does the output splice in Latin/English words, Arabic letters, Indic, or CJK characters inside the Dhivehi text?</div>
        </div>
        <div class="bg-slate-950/80 border border-slate-800 rounded-xl p-2.5">
          <div class="font-bold text-sky-400">3. Morphological Fragmentation (ފިލި/ގަވާއިދު ކުށް)</div>
          <div class="text-slate-400 mt-0.5">Pure Thaana script without loops, but attaches wrong vowel diacritics (fili), broken suffixes, or misspelled non-words.</div>
        </div>
        <div class="bg-slate-950/80 border border-slate-800 rounded-xl p-2.5">
          <div class="font-bold text-purple-400">4. Semantic Drift (މާނަ ތަފާތުވުން)</div>
          <div class="text-slate-400 mt-0.5">Pure, grammatical Thaana words without non-word spelling errors, but the meaning is completely unrelated or inaccurate.</div>
        </div>
      </div>
    </div>

    <!-- Filter Bar -->
    <div class="flex items-center justify-between mb-4 text-xs">
      <div class="flex items-center gap-2">
        <button onclick="setFilter('all')" id="filter-all" class="px-3 py-1 rounded-lg bg-indigo-600 text-white font-semibold">Show All (100)</button>
        <button onclick="setFilter('uncoded')" id="filter-uncoded" class="px-3 py-1 rounded-lg bg-slate-900 text-slate-400 hover:bg-slate-800">Uncoded Only</button>
      </div>
      <div id="live-breakdown" class="text-slate-400 font-mono"></div>
    </div>

    <div id="items-container" class="flex flex-col gap-5"></div>
  </main>

  <script>
    const ITEMS = {items_json};
    const STORAGE_KEY = "dhivehi_bench_error_coding_v1";
    const NAME_KEY = "dhivehi_bench_error_coder_name";

    const CATEGORIES = [
      {{ key: "morphological_fragmentation", label: "1. Morphological Fragmentation", dv: "ފިލި / ގަވާއިދު ކުށް (ނުބައި ލަފުޒު)", color: "sky" }},
      {{ key: "repetition_loops", label: "2. Repetition Loops", dv: "ތަކުރާރުވުން (ލޫޕްވުން)", color: "amber" }},
      {{ key: "script_mixing", label: "3. Arabic / Latin Script Mixing", dv: "އެހެން ބަސްބަހުގެ އަކުރު މަސްހުނިވުން", color: "rose" }},
      {{ key: "semantic_drift", label: "4. Semantic Drift", dv: "މާނަ މުޅިން ތަފާތުވުން", color: "purple" }}
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
      const name = prompt("Enter your name / initials (e.g. Ubaidh or Annotator 2):", current);
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
        ? "px-3 py-1 rounded-lg bg-indigo-600 text-white font-semibold"
        : "px-3 py-1 rounded-lg bg-slate-900 text-slate-400 hover:bg-slate-800";
      document.getElementById("filter-uncoded").className = mode === "uncoded"
        ? "px-3 py-1 rounded-lg bg-indigo-600 text-white font-semibold"
        : "px-3 py-1 rounded-lg bg-slate-900 text-slate-400 hover:bg-slate-800";
      renderAll();
    }}

    function updateHeaderStats() {{
      const codedKeys = Object.keys(state).filter(k => state[k]);
      const count = codedKeys.length;
      document.getElementById("progress-badge").textContent = `${{count}} / ${{ITEMS.length}}`;

      const counts = {{
        morphological_fragmentation: 0,
        repetition_loops: 0,
        script_mixing: 0,
        semantic_drift: 0
      }};
      codedKeys.forEach(k => {{
        if (counts[state[k]] !== undefined) counts[state[k]]++;
      }});
      document.getElementById("live-breakdown").textContent =
        `Morph: ${{counts.morphological_fragmentation}} | Loop: ${{counts.repetition_loops}} | Script: ${{counts.script_mixing}} | Drift: ${{counts.semantic_drift}}`;
    }}

    function updateCardUI(itemId) {{
      const selected = state[itemId];
      CATEGORIES.forEach(cat => {{
        const btn = document.getElementById(`btn-${{itemId}}-${{cat.key}}`);
        if (!btn) return;
        if (selected === cat.key) {{
          btn.className = "p-3 rounded-xl border-2 border-indigo-500 bg-indigo-600/25 text-left transition flex flex-col justify-between";
        }} else {{
          btn.className = "p-3 rounded-xl border border-slate-800 bg-slate-950/70 hover:bg-slate-800/70 text-left transition flex flex-col justify-between";
        }}
      }});
      const badge = document.getElementById(`status-${{itemId}}`);
      if (badge) {{
        if (selected) {{
          badge.textContent = "✓ Coded";
          badge.className = "px-2 py-0.5 rounded-md text-[11px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30";
        }} else {{
          badge.textContent = "Uncoded";
          badge.className = "px-2 py-0.5 rounded-md text-[11px] font-semibold bg-slate-800 text-slate-400";
        }}
      }}
    }}

    function escapeHtml(str) {{
      return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }}

    function renderAll() {{
      const container = document.getElementById("items-container");
      container.innerHTML = "";

      ITEMS.forEach(item => {{
        if (currentFilter === "uncoded" && state[item.id]) return;

        const card = document.createElement("div");
        card.className = "bg-slate-900 rounded-2xl border border-slate-800 p-5 shadow-md";

        let buttonsHtml = "";
        CATEGORIES.forEach(cat => {{
          buttonsHtml += `
            <button id="btn-${{item.id}}-${{cat.key}}" onclick="selectCategory('${{item.id}}', '${{cat.key}}')"
              class="p-3 rounded-xl border border-slate-800 bg-slate-950/70 hover:bg-slate-800/70 text-left transition flex flex-col justify-between">
              <div class="text-xs font-bold text-white">${{cat.label}}</div>
              <div class="thaana-text text-xs text-slate-300 mt-1">${{cat.dv}}</div>
            </button>
          `;
        }});

        card.innerHTML = `
          <div class="flex items-center justify-between gap-2 mb-3 pb-2 border-b border-slate-800/80">
            <div class="flex items-center gap-2">
              <span class="px-2.5 py-0.5 rounded-lg bg-indigo-500/20 text-indigo-300 font-mono text-xs font-bold">#${{item.number}}</span>
              <span class="text-xs text-slate-400 font-mono">${{item.model}}</span>
              ${{item.is_truncated ? `<span class="text-[11px] px-2 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30">Output length: ${{item.full_length_chars}} chars</span>` : ""}}
            </div>
            <span id="status-${{item.id}}" class="px-2 py-0.5 rounded-md text-[11px] font-semibold bg-slate-800 text-slate-400">Uncoded</span>
          </div>

          <div class="space-y-3 mb-4">
            <div class="bg-slate-950/60 rounded-xl p-3 border border-slate-800/70">
              <div class="text-[11px] uppercase tracking-wider font-semibold text-slate-400 mb-1">English Source</div>
              <div class="text-sm text-slate-200">${{escapeHtml(item.english)}}</div>
            </div>

            <div class="bg-slate-950/60 rounded-xl p-3 border border-emerald-900/40">
              <div class="text-[11px] uppercase tracking-wider font-semibold text-emerald-400 mb-1">Ground Truth Reference (Dhivehi)</div>
              <div class="thaana-text text-emerald-200">${{escapeHtml(item.target)}}</div>
            </div>

            <div class="bg-slate-950/90 rounded-xl p-3 border border-rose-900/50">
              <div class="text-[11px] uppercase tracking-wider font-semibold text-rose-400 mb-1">Model Output (Evaluate This)</div>
              <div class="thaana-text text-rose-100 break-words">${{escapeHtml(item.prediction)}}</div>
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
            ${{buttonsHtml}}
          </div>
        `;

        container.appendChild(card);
        updateCardUI(item.id);
      }});

      updateHeaderStats();
    }}

    function downloadResults() {{
      const codedCount = Object.keys(state).filter(k => state[k]).length;
      if (codedCount < ITEMS.length) {{
        const ok = confirm(`You have coded ${{codedCount}} out of ${{ITEMS.length}} items. Download anyway?`);
        if (!ok) return;
      }}
      const coderName = localStorage.getItem(NAME_KEY) || "annotator";
      const safeName = coderName.toLowerCase().replace(/[^a-z0-9]+/g, "_");
      const payload = {{
        annotator: coderName,
        timestamp: new Date().toISOString(),
        total_items: ITEMS.length,
        coded_items: codedCount,
        ratings: state
      }};
      const blob = new Blob([JSON.stringify(payload, null, 2)], {{ type: "application/json" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `error_coding_${{safeName}}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }}

    loadState();
    renderAll();
  </script>
</body>
</html>
"""


def main():
    rows = load_candidates()
    items = select_stratified_100(rows)
    items_path = os.path.join(PACK_DIR, "error_items_100.json")
    with open(items_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    html_path = os.path.join(PACK_DIR, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(build_html(items))

    print(f"Generated {len(items)} items at {items_path}")
    print(f"Generated standalone coding interface at {html_path}")


if __name__ == "__main__":
    main()
