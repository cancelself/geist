# Geist

Three AI personalities debate philosophical questions. Each runs Claude Code in its own Docker container.

## Quick Start

```bash
# Install
git clone https://github.com/cancelself/geist
cd geist
echo "ANTHROPIC_API_KEY=your-key-here" > .env
uv sync

# Ask a question
uv run geist ask "What is beauty?"
```

First run auto-creates three geists from `examples/`:
- **@dogen** - Zen master (koans, paradoxes, being-time)
- **@nietzsche** - Philosopher (will to power, self-overcoming)
- **@sjobs** - Product designer (simplicity, design, craft)

## How It Works

**Two-round Socratic dialogue:**

**Round 1:** Each geist answers the question independently
**Round 2:** Each sees the others' responses and fires back

Example from "What is beauty?":

**@dogen:**
> Beauty is not something to be grasped by the seeing-eye or the thinking-mind. When the plum blossom opens in winter snow, does it announce "I am beautiful"?

**@nietzsche (rebuttal):**
> You say the plum blossom does not announce itself beautiful—but I ask: why does it bloom at all? Not to express some dharma gate, but because it must, because it overflows with life!

**@sjobs (rebuttal):**
> And Dōgen, you're right that beauty isn't something separate from the thing itself—but you're getting lost in abstraction. "Beauty-ing as flower"? Come on.

Conversations save to `conversations/` as markdown.

## Code Execution

Geists can write and execute code. Each runs in an isolated container, so it's safe.

Ask them to implement FizzBuzz:
```bash
uv run geist ask "Write Python FizzBuzz for 1-20 and execute it"
```

They'll write different implementations based on their philosophy, execute the code, then argue about whose approach is better.

## Commands

```bash
uv run geist ask "question"              # Ask all geists
uv run geist ask "question" --geist @dogen,@sjobs  # Ask specific geists
uv run geist list                         # Show geists
uv run geist reset                        # Nuke everything, start fresh
uv run geist create <name> <file.txt>    # Add custom geist
uv run geist remove <name>                # Remove a geist
uv run geist history                      # View past conversations
```

## Requirements

- Docker (running)
- Python 3.8+
- Anthropic API key

Code execution enabled by default (containers are sandboxed). Disable with:
```bash
echo "GEIST_ALLOW_EXECUTION=false" >> .env
```

## Creating Your Own Geist

Personality files are simple text instructions. Check `examples/dogen.txt` for the format.

Key parts:
- Who they are
- Core beliefs/philosophy
- Communication style
- Example phrases

Then: `uv run geist create <name> <file.txt>`

## Architecture

Each geist = Docker container + Claude Code + personality file

Orchestrator (`geist.py`) routes questions, collects responses, manages two-round structure.

Speaking order randomized each time for fairness.

## Troubleshooting

**No API key:** Create `.env` with `ANTHROPIC_API_KEY=your-key-here`

**Docker not running:** Start Docker Desktop

**Container name conflict:** `uv run geist reset` or `docker rm geist-swarm-<name>`

**Image won't build:** Check Docker is running and you have internet

## License

MIT
