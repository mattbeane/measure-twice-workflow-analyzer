#!/usr/bin/env bash
# Measure Twice, Spend Once — one-shot local setup.
# For people who cloned the repo and don't want to fuss with Python tooling.
set -euo pipefail

echo ""
echo "  Measure Twice, Spend Once — setup"
echo "  ---------------------------------"
echo ""

# Prefer uv (fast, handles its own Python). Fall back to pip + venv.
if command -v uv >/dev/null 2>&1; then
    echo "  Using uv..."
    uv sync
    RUN="uv run mtso"
else
    echo "  uv not found — using python venv. (Install uv for a faster setup: https://docs.astral.sh/uv/)"
    if ! command -v python3 >/dev/null 2>&1; then
        echo "  ERROR: python3 not found. Install Python 3.9+ first." >&2
        exit 1
    fi
    python3 -m venv .venv
    # shellcheck disable=SC1091
    source .venv/bin/activate
    python -m pip install --quiet --upgrade pip
    python -m pip install --quiet -e .
    RUN=".venv/bin/mtso"
fi

echo ""
echo "  Setup complete."
echo ""
echo "  Next steps:"
echo "    1. $RUN configure                                  # add your Anthropic API key"
echo "    2. $RUN analyze examples/feature-deploy/workflow.txt --quick   # smoke test"
echo "    3. $RUN analyze your-workflow.txt                  # the real thing"
echo ""
echo "  Full guide: docs/quickstart.md"
echo ""
