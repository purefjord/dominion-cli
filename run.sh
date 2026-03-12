#!/bin/bash
# Run the Dominion CLI evaluation task with Inspect AI
#
# Usage:
#   ./run.sh                          # default: claude-opus-4-6
#   ./run.sh sonnet                   # cheaper: claude-sonnet-4-6
#   ./run.sh opus                     # explicit opus
#
# Prerequisites:
#   1. Set your API key below or as an environment variable
#   2. pip install inspect-ai (already done)

# ============================================================
# SET YOUR API KEY HERE (or export it in your shell profile)
# ============================================================
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo ""
    echo "ERROR: ANTHROPIC_API_KEY is not set."
    echo ""
    echo "Option 1: Export it in your terminal:"
    echo "  export ANTHROPIC_API_KEY=sk-ant-..."
    echo ""
    echo "Option 2: Create a .env file in this directory:"
    echo "  echo 'ANTHROPIC_API_KEY=sk-ant-...' > .env"
    echo ""
    echo "Option 3: Edit this script and set it directly."
    echo ""
    exit 1
fi

# Add inspect CLI to PATH if not already there
INSPECT_DIR="$HOME/AppData/Roaming/Python/Python312/Scripts"
if [ -f "$INSPECT_DIR/inspect.exe" ]; then
    export PATH="$INSPECT_DIR:$PATH"
fi

# Load .env file if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Select model
MODEL="anthropic/claude-opus-4-6"
if [ "$1" = "sonnet" ]; then
    MODEL="anthropic/claude-sonnet-4-6"
elif [ "$1" = "opus" ]; then
    MODEL="anthropic/claude-opus-4-6"
elif [ -n "$1" ]; then
    MODEL="$1"
fi

echo "============================================"
echo " Dominion CLI — Inspect AI Evaluation Run"
echo "============================================"
echo " Model:       $MODEL"
echo " Compaction:   CompactionSummary @ 75%"
echo " Token limit:  10,000,000"
echo " Sandbox:      local"
echo "============================================"
echo ""

# Run the evaluation
cd "$(dirname "$0")"
python -m inspect_ai eval eval_task.py --model "$MODEL"
