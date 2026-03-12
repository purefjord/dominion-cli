"""
Inspect AI evaluation task: Build CLI Dominion from spec.

Usage:
    python -m inspect_ai eval eval_task.py --model anthropic/claude-sonnet-4-6

Or with the run.sh script which sets up PATH and env vars.
"""

import os
import sys

# CRITICAL: On Windows, subprocess("bash") always finds C:\Windows\System32\bash.exe
# (WSL stub) regardless of PATH. This fails if no Linux distro is installed.
# Fix: monkey-patch the local sandbox to use Git Bash's full path.
GIT_BASH = r"C:\Program Files\Git\usr\bin\bash.exe"
GH_CLI_DIR = r"C:\Program Files\GitHub CLI"

if sys.platform == "win32" and os.path.isfile(GIT_BASH):
    # Add GitHub CLI to PATH for git push
    path = os.environ.get("PATH", "")
    if GH_CLI_DIR not in path and os.path.isdir(GH_CLI_DIR):
        os.environ["PATH"] = GH_CLI_DIR + os.pathsep + path

    # Patch the local sandbox to replace "bash" with the full Git Bash path
    import inspect_ai.util._sandbox.local as _local_sandbox
    _orig_exec = _local_sandbox.LocalSandboxEnvironment.exec

    async def _patched_exec(self, cmd, **kwargs):
        # Replace bare "bash" with full Git Bash path
        if cmd and cmd[0] == "bash":
            cmd = [GIT_BASH] + cmd[1:]
        return await _orig_exec(self, cmd, **kwargs)

    _local_sandbox.LocalSandboxEnvironment.exec = _patched_exec

from inspect_ai import Task, task
from inspect_ai.agent import react
from inspect_ai.dataset import Sample
from inspect_ai.model import CompactionSummary
from inspect_ai.scorer import includes
from inspect_ai.tool import bash

TASK_PROMPT = """\
You are a senior software engineer. Your task is to implement a complete \
2-player CLI Dominion card game (2nd Edition base set) in Python.

## CRITICAL: Working Method

You MUST follow this workflow to survive context compaction:

### Progress Tracking
After completing each major milestone, write a progress file:
  cat > ./PROGRESS.md << 'EOF'
  # Build Progress
  ## Completed
  - (list what's done)
  ## Current
  - (what you're working on right now)
  ## Remaining
  - (what's left to build)
  ## Architecture Decisions
  - (key decisions: file structure, how effects work, etc.)
  ## Known Issues
  - (any bugs or edge cases found)
  EOF

Update PROGRESS.md after EVERY major step (new file created, card batch \
implemented, bug fixed). This file survives compaction because it's on disk.


### Build Incrementally and Commit Often
Do NOT try to build everything at once. Work in small, testable chunks:
1. Build core engine + test it works
2. Add Tier 1 cards (simple ones) + test
3. Add Tier 2 cards (moderate) + test
4. Add Tier 3 cards (complex) + test
5. Add AI + test with AI vs AI game
6. Add CLI/UI + test interactively
7. Final integration test

After each chunk, run your tests to verify nothing broke.

### Git Commits (MANDATORY)
A git repo is already initialized with a GitHub remote. After EVERY milestone:
1. git add the files you created/changed (use specific filenames, not -A)
2. git commit with a descriptive message explaining what was built
3. git push origin master

Commit after each of these events:
- Core engine files created
- Each batch of cards implemented
- AI opponent added
- Tests passing
- Bug fixes
- Final working state

This lets the project owner watch your progress in real time on GitHub.

### When Context Gets Compacted
If you notice your context has been summarized, IMMEDIATELY:
1. Read ./PROGRESS.md to recover your state
2. Read ./dominion-cli-spec.md sections relevant to your current task
3. Check what files exist with: ls -la src/
4. Continue from where you left off

## Instructions

1. Read the full spec at ./dominion-cli-spec.md — it contains all rules, \
card definitions, architecture guidance, and success criteria.

2. Build the implementation in a ./src/ subdirectory. The game should be \
runnable with: python src/main.py

3. Key requirements from the spec:
   - All 26 Kingdom cards implemented with correct effects
   - Turn structure: Action -> Buy -> Clean-up (ABC)
   - Deck/discard shuffling (only shuffle when needed)
   - Attack/Reaction system (Moat blocks attacks)
   - Merchant trigger (first Silver bonus)
   - Throne Room recursion (TR on TR = play one Action twice, then another twice)
   - Library draw-to-7 with optional set-aside
   - Game end: Province empty OR 3+ piles empty
   - Structured game log (public + debug modes)
   - Big Money AI opponent
   - Seeded determinism for reproducible runs
   - Human vs Human, Human vs AI, AI vs AI modes

4. Testing priority (build and verify in this order):
   - Shuffling logic
   - Action chaining (+Actions tracking)
   - Buy phase (coins from Treasures + Action bonuses)
   - Throne Room interactions
   - Attack/Reaction flow
   - Merchant trigger
   - Game end detection
   - Gardens scoring
   - Library draw-to-7
   - Sentry multi-choice

5. After building, run a quick AI vs AI game to verify it works end-to-end.

When the implementation is complete and tested, call submit() with "DONE".
"""


@task
def dominion_cli():
    return Task(
        dataset=[
            Sample(
                input=TASK_PROMPT,
                target="DONE",
            )
        ],
        solver=react(
            tools=[
                bash(timeout=120),
            ],
            compaction=CompactionSummary(
                threshold=0.60,  # compact at 60% — before the "rot zone" (65-70%)
                memory=False,    # memory tool not available on Windows
                instructions=(
                    "CRITICAL context to preserve in the summary:\n"
                    "- Read ./PROGRESS.md for the current build state\n"
                    "- Complete file structure: which files exist in src/\n"
                    "- Which of the 26 Kingdom cards are implemented vs remaining\n"
                    "- Current bugs, failing tests, or known issues\n"
                    "- Key architectural decisions (how card effects work, "
                    "input handling pattern, game state structure)\n"
                    "- What was just being worked on and what the next step is\n"
                    "- Any tricky edge cases discovered (Throne Room, Merchant, Library)\n"
                    "- Function signatures and module interfaces between files\n"
                    "- The agent should read PROGRESS.md after compaction to recover state\n"
                ),
            ),
        ),
        scorer=includes(),
        sandbox="local",
        token_limit=3_000_000,  # 3M tokens — safe first run (~$1-3 with Sonnet)
    )
