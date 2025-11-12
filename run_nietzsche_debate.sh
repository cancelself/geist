#!/bin/bash
# Quick script to run the Nietzsche/AI debate

echo "Starting Nietzsche/AI debate with all Geists..."
echo "=============================================="
echo ""

# Read the debate prompt and pass it to geist
uv run geist ask "$(cat debate_nietzsche_ai.txt)"

echo ""
echo "Debate complete! Check the conversations/ directory for the saved dialogue."
