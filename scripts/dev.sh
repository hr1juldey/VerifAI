#!/usr/bin/env bash
# VerifAI dev server with hot reload in tmux
# Usage: ./scripts/dev.sh
set -euo pipefail

SESSION="verifai"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Kill existing session if any
tmux kill-session -t "$SESSION" 2>/dev/null || true

# Create new session with 2 panes
tmux new-session -d -s "$SESSION" -c "$REPO_ROOT"

# Pane 0: FastAPI dev server with hot reload
tmux send-keys -t "$SESSION:0.0" \
    "cd '$REPO_ROOT' && uv run uvicorn app.presentation.main:app --reload --reload-dir app/ --log-config log_config.json" \
    Enter

# Pane 1: Interactive shell for tests
tmux split-window -h -t "$SESSION:0.0" -c "$REPO_ROOT"

echo "VerifAI dev session started!"
echo "  Attach:  tmux attach -t $SESSION"
echo "  Kill:    tmux kill-session -t $SESSION"
echo ""
echo "  Pane 0: FastAPI server (hot reload on app/)"
echo "  Pane 1: Shell (run tests with: uv run pytest -m gpu)"
