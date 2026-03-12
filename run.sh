#!/bin/bash
# Run the Dominion CLI evaluation task with Inspect AI
#
# Usage:
#   ./run.sh                          # default: claude-sonnet-4-6
#   ./run.sh sonnet                   # cheaper: claude-sonnet-4-6
#   ./run.sh opus                     # full power: claude-opus-4-6
#
# Prerequisites:
#   1. Set your API key in .env or as an environment variable
#   2. pip install inspect-ai (already done)
#   3. gh auth login (already done)

# Load .env file if it exists (must come first so API key is available)
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

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
    exit 1
fi

# Add tools to PATH
INSPECT_DIR="$HOME/AppData/Roaming/Python/Python312/Scripts"
if [ -f "$INSPECT_DIR/inspect.exe" ]; then
    export PATH="$INSPECT_DIR:$PATH"
fi

# Add GitHub CLI to PATH so the agent can git push
GH_DIR="/c/Program Files/GitHub CLI"
if [ -d "$GH_DIR" ]; then
    export PATH="$GH_DIR:$PATH"
fi

# Select model
MODEL="anthropic/claude-sonnet-4-6"
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
echo " Compaction:  CompactionSummary @ 60%"
echo " Token limit: 3,000,000"
echo " Sandbox:     local"
echo " GitHub:      https://github.com/purefjord/dominion-cli"
echo "============================================"
echo ""

# Run the evaluation
cd "$(dirname "$0")"
python -m inspect_ai eval eval_task.py --model "$MODEL"
