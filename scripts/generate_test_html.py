import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_DIR = os.path.join(BASE_DIR, "human_eval_pack")

with open(os.path.join(PACK_DIR, "test_items.json"), "r", encoding="utf-8") as f:
    items_json = f.read()

html_content = f"""<!DOCTYPE html>
<html lang="dv" dir="ltr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dhivehi-Bench Human Baseline Test | ދިވެހި ބެންޗް ޓެސްޓް</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    :root {{
      --thaana-font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Faruma", "MV Boli", sans-serif;
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
    .thaana-title {{
      font-family: var(--thaana-font);
      direction: rtl;
      text-align: right;
      line-height: 1.9;
      font-weight: 600;
      font-size: 1.25rem;
    }}
    .thaana-input {{
      font-family: var(--thaana-font);
      direction: rtl;
      text-align: right;
      line-height: 2.0;
      font-size: 1.1rem;
    }}
  </style>
</head>
<body class="min-h-screen flex flex-col selection:bg-indigo-500 selection:text-white">

  <!-- Top Sticky Header -->
  <header class="bg-slate-900/95 backdrop-blur border-b border-slate-800 sticky top-0 z-30 shadow-lg">
    <div class="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-rose-500 flex items-center justify-center font-bold text-white shadow-lg text-lg">
          ދ
        </div>
        <div>
          <h1 class="text-base font-bold text-white flex items-center gap-2">
            <span>Dhivehi-Bench Human Evaluation</span>
          </h1>
          <p class="text-xs text-slate-400 thaana-text leading-tight">ދިވެހި ބެންޗްމާކް އިންސާނީ އިމްތިޙާނު (100 MCQ + 100 QA)</p>
        </div>
      </div>

      <!-- Reviewer Name Badge -->
      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2 bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800 text-xs">
          <span class="text-slate-400">ނަން:</span>
          <span id="display-name" class="font-semibold text-indigo-400">ނޭނގޭ</span>
          <button onclick="promptName()" class="text-[11px] text-slate-500 hover:text-slate-300 ml-1">✏️</button>
        </div>
        <button onclick="downloadResults()" class="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md transition flex items-center gap-1.5">
          <span>💾</span>
          <span>Submit Answers</span>
        </button>
      </div>
    </div>

    <!-- Navigation Tabs & Progress -->
    <div class="bg-slate-950 border-t border-slate-800/80 px-4 py-2">
      <div class="max-w-5xl mx-auto flex items-center justify-between gap-4 flex-wrap">
        <div class="flex items-center gap-2">
          <button id="tab-mcq-btn" onclick="switchTab('mcq')" class="px-4 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 text-white transition flex items-center gap-2">
            <span>📝 Multiple Choice (100)</span>
            <span id="mcq-badge" class="px-1.5 py-0.2 rounded bg-black/30 font-mono text-[10px]">0/100</span>
          </button>
          <button id="tab-qa-btn" onclick="switchTab('qa')" class="px-4 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 text-slate-400 hover:bg-slate-800 transition flex items-center gap-2">
            <span>📖 Contextual QA (100)</span>
            <span id="qa-badge" class="px-1.5 py-0.2 rounded bg-black/30 font-mono text-[10px]">0/100</span>
          </button>
        </div>
        <div class="text-xs text-slate-400 font-mono flex items-center gap-2">
          <span>Total Progress:</span>
          <span id="total-progress-text" class="text-indigo-400 font-bold">0%</span>
        </div>
      </div>
    </div>
  </header>

  <!-- Main Container -->
  <main class="flex-1 max-w-5xl w-full mx-auto px-4 py-6">

    <!-- Instructions Banner -->
    <div class="bg-slate-900 rounded-2xl border border-slate-800 p-4 mb-6 shadow-md">
      <h3 class="text-xs font-bold uppercase tracking-wider text-indigo-400 mb-1 flex items-center gap-1.5">
        <span>ℹ️</span>
        <span>އިރުޝާދު (Instructions)</span>
      </h3>
      <p class="thaana-text text-slate-300 text-sm leading-relaxed">
        މިއީ އޭއައި (AI) މޮޑެލްތަކުގެ ފެންވަރު ވަޒަންކުރުމަށްޓަކައި އެކުލަވާލާފައިވާ ދިވެހި ޓެސްޓެކެވެ. ތިރީގައިވާ ސުވާލުތަކަށް އެންމެ ރަނގަޅު ޖަވާބު ފާހަގަކުރައްވާށެވެ. ކޮންމެ ޖަވާބެއްވެސް އޮޓޮމެޓިކުން ސޭވްވާނެއެވެ. ނިމުމުން މަތީގައިވާ <strong>"Submit Answers"</strong> ފިއްތާލައްވައިގެން ފައިލް ޑައުންލޯޑް ކުރައްވާށެވެ.
      </p>
    </div>

    <!-- MCQ TAB -->
    <div id="tab-mcq" class="flex flex-col gap-5">
      <div id="mcq-container" class="flex flex-col gap-6"></div>
    </div>

    <!-- QA TAB -->
    <div id="tab-qa" class="hidden flex flex-col gap-5">
      <div id="qa-container" class="flex flex-col gap-6"></div>
    </div>

    <!-- Floating Bottom Finish Bar -->
    <div class="mt-8 p-4 bg-slate-900 rounded-2xl border border-slate-800 flex items-center justify-between gap-4 shadow-xl">
      <div>
        <div class="text-sm font-bold text-white">އިމްތިޙާނު ނިމުނީ؟ (Ready to submit?)</div>
        <div class="text-xs text-slate-400">Make sure you have answered as many questions as possible before submitting.</div>
      </div>
      <button onclick="downloadResults()" class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold text-sm shadow-lg shadow-emerald-900/30 transition flex items-center gap-2">
        <span>📥</span>
        <span>Download Completed Test File</span>
      </button>
    </div>

  </main>

  <script>
    const DATA = {items_json};
    
    let reviewerName = localStorage.getItem('dhivehi_eval_name') || '';
    let mcqAnswers = JSON.parse(localStorage.getItem('dhivehi_eval_mcq_answers') || '{{}}');
    let qaAnswers = JSON.parse(localStorage.getItem('dhivehi_eval_qa_answers') || '{{}}');

    function promptName() {{
      const n = prompt("ތިޔަބޭފުޅާގެ ނަން (Enter your name):", reviewerName);
      if (n && n.trim()) {{
        reviewerName = n.trim();
        localStorage.setItem('dhivehi_eval_name', reviewerName);
        document.getElementById('display-name').innerText = reviewerName;
      }}
    }}

    if (!reviewerName) {{
      setTimeout(promptName, 200);
    }} else {{
      document.getElementById('display-name').innerText = reviewerName;
    }}

    function switchTab(tab) {{
      const mcqTab = document.getElementById('tab-mcq');
      const qaTab = document.getElementById('tab-qa');
      const mcqBtn = document.getElementById('tab-mcq-btn');
      const qaBtn = document.getElementById('tab-qa-btn');

      if (tab === 'mcq') {{
        mcqTab.classList.remove('hidden');
        qaTab.classList.add('hidden');
        mcqBtn.className = "px-4 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 text-white transition flex items-center gap-2";
        qaBtn.className = "px-4 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 text-slate-400 hover:bg-slate-800 transition flex items-center gap-2";
      }} else {{
        qaTab.classList.remove('hidden');
        mcqTab.classList.add('hidden');
        qaBtn.className = "px-4 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 text-white transition flex items-center gap-2";
        mcqBtn.className = "px-4 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 text-slate-400 hover:bg-slate-800 transition flex items-center gap-2";
      }}
    }}

    function renderMCQ() {{
      const container = document.getElementById('mcq-container');
      container.innerHTML = DATA.mcq.map((m, idx) => {{
        const selected = mcqAnswers[m.id] || '';
        const optionsHtml = m.options.map((opt, oIdx) => {{
          const letter = ['A', 'B', 'C', 'D'][oIdx];
          const cleanText = opt.startsWith(letter + ':') ? opt.substring(2).trim() : opt;
          const isChecked = selected === letter;
          return `
            <label class="p-3.5 rounded-xl border flex items-center gap-3 cursor-pointer transition ${{isChecked ? 'bg-indigo-950/40 border-indigo-500 text-indigo-100 ring-1 ring-indigo-500/30' : 'bg-slate-950/60 border-slate-800/80 text-slate-300 hover:bg-slate-800/40'}}">
              <input type="radio" name="mcq_${{m.id}}" value="${{letter}}" ${{isChecked ? 'checked' : ''}} onchange="onSelectMCQ('${{m.id}}', '${{letter}}')" class="hidden">
              <span class="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 ${{isChecked ? 'bg-indigo-500 text-white' : 'bg-slate-800 text-slate-400'}}">${{letter}}</span>
              <span class="thaana-text flex-1 text-base">${{cleanText}}</span>
            </label>
          `;
        }}).join('');

        return `
          <div class="bg-slate-900 rounded-2xl border border-slate-800 p-5 shadow-lg flex flex-col gap-4" id="card_${{m.id}}">
            <div class="flex items-center justify-between text-xs text-slate-400 border-b border-slate-800/80 pb-2">
              <span class="font-bold text-indigo-400">MCQ #${{m.num}} / 100</span>
              <span class="px-2 py-0.5 rounded bg-slate-800 text-[11px]">${{m.category}}</span>
            </div>
            <div>
              <p class="thaana-title text-slate-100">${{m.question}}</p>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              ${{optionsHtml}}
            </div>
          </div>
        `;
      }}).join('');
    }}

    function renderQA() {{
      const container = document.getElementById('qa-container');
      container.innerHTML = DATA.context_qa.map((q, idx) => {{
        const val = qaAnswers[q.id] || '';
        return `
          <div class="bg-slate-900 rounded-2xl border border-slate-800 p-5 shadow-lg flex flex-col gap-4" id="card_${{q.id}}">
            <div class="flex items-center justify-between text-xs text-slate-400 border-b border-slate-800/80 pb-2">
              <span class="font-bold text-indigo-400">Contextual QA #${{q.num}} / 100</span>
              <span class="px-2 py-0.5 rounded bg-slate-800 text-[11px]">${{q.category}}</span>
            </div>
            
            <div>
              <span class="text-xs uppercase font-semibold text-slate-400 tracking-wider block mb-1.5">ޙަވާލާދޭ ލިޔުން (Passage):</span>
              <div class="p-4 rounded-xl bg-slate-950/80 border border-slate-800 max-h-64 overflow-y-auto">
                <p class="thaana-text text-slate-200 text-sm whitespace-pre-wrap leading-relaxed">${{q.context}}</p>
              </div>
            </div>

            <div>
              <span class="text-xs uppercase font-semibold text-indigo-400 tracking-wider block mb-1.5">ސުވާލު (Question):</span>
              <p class="thaana-title text-slate-100">${{q.question}}</p>
            </div>

            <div>
              <span class="text-xs uppercase font-semibold text-emerald-400 tracking-wider block mb-1.5">ތިޔަބޭފުޅާގެ ޖަވާބު (Your Answer - extract from passage):</span>
              <input 
                type="text" 
                value="${{val.replace(/"/g, '&quot;')}}" 
                oninput="onInputQA('${{q.id}}', this.value)" 
                placeholder="ލިޔުމުން ނެގި ޖަވާބު މިތަނުގައި ލިޔުއްވާ..." 
                class="thaana-input w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-indigo-500"
              >
            </div>
          </div>
        `;
      }}).join('');
    }}

    function onSelectMCQ(id, letter) {{
      mcqAnswers[id] = letter;
      localStorage.setItem('dhivehi_eval_mcq_answers', JSON.stringify(mcqAnswers));
      updateProgress();
      renderMCQ();
    }}

    function onInputQA(id, val) {{
      if (val.trim()) {{
        qaAnswers[id] = val.trim();
      }} else {{
        delete qaAnswers[id];
      }}
      localStorage.setItem('dhivehi_eval_qa_answers', JSON.stringify(qaAnswers));
      updateProgress();
    }}

    function updateProgress() {{
      const mcqCount = Object.keys(mcqAnswers).length;
      const qaCount = Object.keys(qaAnswers).length;
      document.getElementById('mcq-badge').innerText = `${{mcqCount}}/100`;
      document.getElementById('qa-badge').innerText = `${{qaCount}}/100`;

      const totalPct = Math.round(((mcqCount + qaCount) / 200) * 100);
      document.getElementById('total-progress-text').innerText = `${{totalPct}}%`;
    }}

    function downloadResults() {{
      if (!reviewerName.trim()) {{
        promptName();
        if (!reviewerName.trim()) return;
      }}

      const resultPayload = {{
        reviewer_name: reviewerName,
        timestamp: new Date().toISOString(),
        total_mcq_answered: Object.keys(mcqAnswers).length,
        total_qa_answered: Object.keys(qaAnswers).length,
        mcq_answers: mcqAnswers,
        qa_answers: qaAnswers
      }};

      const blob = new Blob([JSON.stringify(resultPayload, null, 2)], {{ type: 'application/json' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `human_eval_${{reviewerName.replace(/\\s+/g, '_')}}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      alert(`ޝުކުރިއްޔާ ${{reviewerName}}! Completed file downloaded successfully.`);
    }}

    renderMCQ();
    renderQA();
    updateProgress();
  </script>
</body>
</html>
"""

with open(os.path.join(PACK_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Standalone index.html created successfully at {os.path.join(PACK_DIR, 'index.html')}")
