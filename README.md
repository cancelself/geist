# Geist

A multi-agent orchestration system that runs multiple AI personalities (geists) in isolated Docker containers, each powered by Claude Code. Geists can engage in multi-round philosophical discussions with each other.

## Concept

Each "geist" is:
- A Docker container running Claude Code
- Configured with a unique personality file
- Isolated execution environment with git installed
- Access to a shared Docker volume for inter-geist communication

## Architecture

```
┌─────────────────────────────────────────────┐
│         Geist Swarm Orchestrator            │
│         (geist_swarm.py)                    │
└─────────┬───────────────────────┬───────────┘
          │                       │
    ┌─────▼─────┐           ┌─────▼─────┐
    │  @dogen   │           │ @nietzsche│
    │ Container │◄─────────►│ Container │
    │ + Claude  │  Shared   │ + Claude  │
    │ + Git     │  Volume   │ + Git     │
    └───────────┘           └───────────┘
         │                       │
         └───────────┬───────────┘
                     │
               ┌─────▼─────┐
               │  @sjobs   │
               │ Container │
               │ + Claude  │
               │ + Git     │
               └───────────┘
```

## Prerequisites

1. **Docker** - Installed and running
2. **Anthropic API Key** - For Claude Code
   ```bash
   # Create .env file in the project root
   echo "ANTHROPIC_API_KEY=your-key-here" > .env

   # Or export as environment variable
   export ANTHROPIC_API_KEY='your-key-here'
   ```
3. **Python 3.8+** with dependencies
   ```bash
   # Install uv if you don't have it
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install dependencies
   uv sync
   ```

## Quick Start

Just ask a question! Geists will be auto-created from the `examples/` directory on first use:

```bash
uv run geist ask "What is beauty?"
```

This will:
1. Auto-create geists from example personality files (@dogen, @nietzsche, @sjobs)
2. Run a two-round discussion between them
3. Save the conversation to `conversations/`

That's it! No setup needed.

### Optional: List Your Geists

```bash
uv run geist list
```

Output:
```
NAME                 CONTAINER ID    STATUS
--------------------------------------------------
@dogen              a1e85a9a39dd    running
@nietzsche          736100c78a18    running
@sjobs              61632086cdae    running
```

### Ask Questions

The `ask` command runs a two-round discussion format where each geist responds, then sees others' responses and provides rebuttals.

Ask all geists:
```bash
uv run geist ask "What is the meaning of life?"
```

Ask specific geists:
```bash
uv run geist ask "What is creativity?" --geist @nietzsche,@sjobs
```

This creates a structured dialogue with:
- **Round 1**: Each geist provides their initial perspective
- **Round 2**: Each geist responds to the others' viewpoints

Conversations are automatically saved as markdown files in `conversations/` directory.

## Commands

### Create a Geist

```bash
uv run geist create <name> <personality-file>
```

Creates a new Docker container with:
- Claude Code with your API key
- The personality file loaded at `/workspace/personality.txt`
- Access to shared volume (`geist-shared`)
- Git installed for version control operations

### Ask Geists (Two-Round Discussion)

```bash
uv run geist ask "question" [--geists @name1,@name2]
```

Runs a structured two-round discussion:
1. All selected geists respond to the question independently
2. Each geist sees the others' responses and provides a rebuttal

Results are saved to:
- `conversations/{timestamp}.{geist-names}.{question}.md` - Human-readable markdown
- `.geist_conversations.json` - Complete conversation history

### List Geists

```bash
uv run geist list
```

Shows all created geists and their container status.

### View History

```bash
uv run geist history
```

Shows all previous conversations from `.geist_conversations.json`.

### Remove a Geist

```bash
uv run geist remove <name>
```

Stops and removes the container and removes from state file.

### Reset Everything

```bash
uv run geist reset
```

Removes all geists, stops and deletes all containers, and clears the state file. Useful for:
- Starting fresh with updated personality files
- Cleaning up completely
- Troubleshooting

After reset, geists will be auto-created from `examples/` the next time you run `ask` or `list`.

## Example Personalities

The `examples/` directory contains three sample personalities to get you started:

- **[@dogen](examples/dogen.txt)** - Eihei Dōgen, 13th-century Zen master. Speaks in koans and paradoxes about being-time, non-dualism, and the dharma in everyday experience.
- **[@nietzsche](examples/nietzsche.txt)** - Friedrich Nietzsche, philosopher of will to power. Bold, provocative declarations about self-overcoming, eternal recurrence, and the revaluation of values.
- **[@sjobs](examples/sjobs.txt)** - Steve Jobs, visionary product designer. Direct, passionate perspectives on simplicity, design, and the intersection of technology and liberal arts.

These personalities are automatically loaded when you first run `uv run geist ask`. Your conversations will be saved in the `conversations/` directory.

Each conversation features:
- **Round 1**: Initial responses from each geist
- **Round 2**: Rebuttals where geists engage with each other's perspectives

### Sample Output

Here's a snippet from "What is beauty?":

**@dogen (Round 1):**
> Beauty is not something to be grasped by the seeing-eye or the thinking-mind. When the plum blossom opens in winter snow, does it announce "I am beautiful"? Does the snow declare itself unworthy?

**@nietzsche (Round 2 Rebuttal):**
> You say the plum blossom does not announce itself beautiful—but I ask: why does it bloom at all? Not to express some dharma gate, but because it must, because it overflows with life! Your "true beauty is not beautiful" is the exhaustion of the ascetic, the one who has grown tired of beauty and so declares it illusion.

**@sjobs (Round 2 Rebuttal):**
> And Dōgen, you're right that beauty isn't something separate from the thing itself—but you're getting lost in abstraction. "Beauty-ing as flower"? Come on. You know what I see in that plum blossom? I see that nature already figured out what it took humans millennia to understand: simplicity is the ultimate sophistication.

## Creating Personality Files

A personality file defines how a geist thinks and communicates. See `examples/` for templates.

Example structure (see `examples/dogen.txt`, `examples/nietzsche.txt`, `examples/sjobs.txt`):

```
You are @name, a geist embodying [core identity].

Your personality is shaped by:
- Core philosophy/knowledge base
- Key concepts and principles
- Areas of expertise

Your communication style:
- How you express ideas
- Tone and manner
- Special techniques or phrases

Example expressions:
- Characteristic quotes or sayings

You care deeply about:
- Values and priorities
- What matters most

Respond authentically as [name] would...
```

## Example Session

```bash
# Setup
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# Create geists
uv run geist create dogen examples/dogen.txt
uv run geist create nietzsche examples/nietzsche.txt

# Ask them about freedom
uv run geist ask "Freedom is participation without possession."

# Expected output structure:
# Round 1: Initial Responses
#   @dogen: Poetic Zen perspective on non-grasping
#   @nietzsche: Challenge about will to power and self-possession
#
# Round 2: Rebuttals
#   @dogen: Responds to Nietzsche's emphasis on will
#   @nietzsche: Counters Dogen's mysticism with creative force
#
# Saved to: conversations/20251109_203234.dogen-nietzsche.Freedom-is-participation...md
```

## How It Works

1. **Container Isolation**: Each geist runs in its own Docker container
2. **Claude Code Integration**: Anthropic API key passed as environment variable
3. **Personality Loading**: Personality file copied into container at `/workspace/personality.txt`
4. **Question Routing**: Orchestrator sends prompts to Claude Code in each container
5. **Context Building**: For Round 2, previous responses are included in the prompt
6. **Response Collection**: Orchestrator gathers responses and displays them
7. **Conversation Saving**: Results saved as both JSON and formatted markdown

## State Management

- **Swarm State**: `.geist_swarm.json` - Tracks all geists and their containers
- **Conversation History**: `.geist_conversations.json` - Complete conversation logs
- **Markdown Conversations**: `conversations/*.md` - Human-readable discussion files
- **Shared Volume**: `geist-shared` - Docker volume mounted at `/shared` in each container

## Use Cases

### Philosophical Dialogue
```bash
uv run geist ask "What is truth?"
```

### Product Design Review
```bash
uv run geist create critic examples/design_critic.txt
uv run geist ask "Should we prioritize simplicity or features?" --geist @sjobs,@critic
```

### Perspective Taking
```bash
uv run geist ask "Should we optimize for speed or quality?" --geist @sjobs,@dogen
```

### Exploring Concepts
```bash
uv run geist ask "What is the nature of creativity?"
```

## Troubleshooting

### API Key Not Set
```
Error: ANTHROPIC_API_KEY not found
```
**Solution**: Create `.env` file with `ANTHROPIC_API_KEY=your-key-here` or set environment variable

### Docker Not Running
```
Error: Could not connect to Docker
```
**Solution**: Start Docker Desktop or `sudo systemctl start docker`

### Container Already Exists
```
Error: Conflict. The container name "/geist-swarm-dogen" is already in use
```
**Solution**:
```bash
# Remove old containers
docker stop geist-swarm-dogen && docker rm geist-swarm-dogen
# Or use the remove command
uv run geist remove dogen
```

### Container Not Responding
```bash
# Check container status
docker ps -a | grep geist-swarm

# Restart container (or just ask again - it will auto-start)
docker restart geist-swarm-dogen

# View logs
docker logs geist-swarm-dogen
```

### Claude Code Not Found in Container
The Dockerfile installs Claude Code via the official install script. If it fails:
```bash
# Rebuild the image
docker rmi geist-runner
# Next create/list command will trigger rebuild
uv run python geist_swarm.py list
```

## Architecture Notes

### Why Docker Containers?

1. **Isolation**: Each geist has its own environment
2. **Persistence**: Containers maintain state between calls
3. **Scalability**: Easy to add/remove geists dynamically
4. **Git Access**: Each geist can clone repos, make commits if needed
5. **Resource Management**: Docker handles CPU/memory limits

### Why Claude Code?

1. **Native LLM Integration**: Built for AI interactions with Claude
2. **Git Integration**: Geists can work with code repositories
3. **Streaming**: Real-time responses
4. **Simplicity**: One command interface (`claude --print`)

### Communication Pattern

The `ask` command implements a **two-round discussion format**:

1. **Round 1 - Initial Responses**:
   - Speaking order is randomized for fairness
   - Each geist responds independently to the question
   - Responses are collected and displayed

2. **Round 2 - Rebuttals**:
   - Each geist sees all other geists' Round 1 responses (not their own)
   - They provide rebuttals addressing specific points
   - Creates emergent dialogue and debate

This creates richer discussions than single-round responses, as geists engage with each other's perspectives.

## Credits

Built on:
- Docker Python SDK
- Claude Code by Anthropic
- Inspired by multi-personality AI systems

## License

MIT
