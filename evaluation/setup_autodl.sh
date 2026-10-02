#!/bin/bash
# 1. Bypass Great Firewall for python and HF
export HF_ENDPOINT=https://hf-mirror.com
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 2. Install Harness and vLLM
git clone https://github.com/EleutherAI/lm-evaluation-harness
cd lm-evaluation-harness
pip install -e .
pip install vllm sacrebleu rouge_score

# 3. Copy our tasks into the harness
mkdir -p lm_eval/tasks/dhivehi_bench
cp ../dhivehi_*.yaml lm_eval/tasks/dhivehi_bench/

echo "✅ Environment setup complete! You can now run evaluations using vLLM."
