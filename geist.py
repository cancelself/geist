#!/usr/bin/env python3
"""
Geist Swarm - Multi-agent orchestration system

Each geist runs in its own Docker container with Claude Code and a personality file.
Geists communicate by reading/writing to a shared message queue.

Usage:
    python geist.py create <name> <personality-file>         - Create a new geist
    python geist.py list                                      - List all geists
    python geist.py ask "question" [--geist @a,@b]            - Ask specific geists
    python geist.py converse "topic" --rounds 3               - Multi-round conversation
    python geist.py debate "topic" --for @a --against @b      - Structured debate
    python geist.py remove <name>                             - Remove a geist
    python geist.py reset                                     - Remove all geists and state
    python geist.py history                                   - View conversation history

Setup:
    1. Set ANTHROPIC_API_KEY environment variable
    2. Create personality files (see examples/)
    3. Create geists: python geist.py create dogen dogen.txt
"""

import sys
import json
import docker
import os
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

SWARM_IMAGE = "geist-runner"
CONTAINER_PREFIX = "geist-swarm"
STATE_FILE = Path(".geist_swarm.json")
CONVERSATION_FILE = Path(".geist_conversations.json")
SHARED_VOLUME = "geist-shared"


class GeistSwarm:
    def __init__(self):
        # Load .env file if it exists
        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        # Check for API key
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("Error: ANTHROPIC_API_KEY not found")
            print("Create a .env file with: ANTHROPIC_API_KEY=your-key-here")
            print("Or set environment variable: export ANTHROPIC_API_KEY='your-key-here'")
            sys.exit(1)

        try:
            # Try macOS Docker Desktop socket first
            docker_socket = Path.home() / ".docker" / "run" / "docker.sock"
            if docker_socket.exists():
                self.client = docker.DockerClient(base_url=f"unix://{docker_socket}")
            else:
                # Fall back to default
                self.client = docker.from_env()
        except docker.errors.DockerException as e:
            print(f"Error: Could not connect to Docker. Is Docker running?")
            print(f"Details: {e}")
            sys.exit(1)

        self.ensure_image()
        self.ensure_shared_volume()

    def ensure_image(self):
        """Ensure the Docker image exists"""
        try:
            self.client.images.get(SWARM_IMAGE)
        except docker.errors.ImageNotFound:
            print(f"Building Docker image: {SWARM_IMAGE}...")
            dockerfile_dir = Path(__file__).parent
            try:
                self.client.images.build(
                    path=str(dockerfile_dir),
                    tag=SWARM_IMAGE,
                    rm=True
                )
                print(f"Successfully built image: {SWARM_IMAGE}")
            except docker.errors.BuildError as e:
                print(f"Error building Docker image: {e}")
                sys.exit(1)

    def ensure_shared_volume(self):
        """Create a shared Docker volume for inter-geist communication"""
        try:
            self.client.volumes.get(SHARED_VOLUME)
        except docker.errors.NotFound:
            self.client.volumes.create(SHARED_VOLUME)
            print(f"Created shared volume: {SHARED_VOLUME}")

    def save_state(self, state):
        """Save swarm state to file"""
        STATE_FILE.write_text(json.dumps(state, indent=2))

    def load_state(self):
        """Load swarm state from file"""
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
        return {"geists": {}}

    def ensure_default_geists(self):
        """Auto-create geists from examples/ directory if none exist"""
        state = self.load_state()

        # If we already have geists, do nothing
        if state["geists"]:
            return

        # Look for example personality files
        examples_dir = Path(__file__).parent / "examples"
        if not examples_dir.exists():
            return

        personality_files = list(examples_dir.glob("*.txt"))
        if not personality_files:
            return

        print("No geists found. Auto-creating geists from examples/...")
        print()

        for personality_file in personality_files:
            # Extract name from filename (e.g., "dogen.txt" -> "dogen")
            name = personality_file.stem
            try:
                self.create_geist(name, str(personality_file))
            except Exception as e:
                print(f"Warning: Failed to create {name}: {e}")

        print()
        print(f"Created {len(personality_files)} geists. Ready to go!")
        print()

    def save_conversation(self, conversation):
        """Save conversation history"""
        conversations = []
        if CONVERSATION_FILE.exists():
            conversations = json.loads(CONVERSATION_FILE.read_text())

        conversations.append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "conversation": conversation
        })

        CONVERSATION_FILE.write_text(json.dumps(conversations, indent=2))

    def save_conversation_as_markdown(self, question, debate_log, geist_names):
        """Save conversation as a Socratic dialog markdown file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create filename: {datetime}.{geist-names}.{question}.md
        geists_part = "-".join([name.lstrip("@") for name in geist_names])

        # Sanitize question for filename (limit length, remove special chars)
        question_part = question[:50].replace(" ", "-").replace("/", "-")
        question_part = "".join(c for c in question_part if c.isalnum() or c in "-_")

        filename = f"{timestamp}.{geists_part}.{question_part}.md"

        # Create conversations directory if it doesn't exist
        conversations_dir = Path("conversations")
        conversations_dir.mkdir(exist_ok=True)

        filepath = conversations_dir / filename

        # Build markdown content
        md_content = f"""# Socratic Dialog: {question}

**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Participants:** {", ".join(geist_names)}

---

"""

        # Group by rounds
        round_1 = []
        round_2 = []

        for entry in debate_log:
            if "Rebuttal" in str(entry.get("question", "")):
                round_2.append(entry)
            else:
                round_1.append(entry)

        # Round 1: Initial Responses
        if round_1:
            md_content += "## Round 1: Initial Responses\n\n"
            for entry in round_1:
                name = entry.get("name", "Unknown")
                content = entry.get("content", "")
                md_content += f"### {name}\n\n"
                md_content += f"> {content.strip()}\n\n"
                md_content += "---\n\n"

        # Round 2: Rebuttals
        if round_2:
            md_content += "## Round 2: Rebuttals\n\n"
            for entry in round_2:
                name = entry.get("name", "Unknown")
                content = entry.get("content", "")
                md_content += f"### {name} - Rebuttal\n\n"
                md_content += f"*In response to the previous perspectives:*\n\n"
                md_content += f"> {content.strip()}\n\n"
                md_content += "---\n\n"

        # Write to file
        filepath.write_text(md_content)

        return filepath

    def create_geist(self, name, personality_file):
        """Create a new geist container with a specific personality"""
        if not os.path.exists(personality_file):
            print(f"Error: Personality file not found: {personality_file}")
            sys.exit(1)

        # Ensure name starts with @
        if not name.startswith("@"):
            name = f"@{name}"

        state = self.load_state()

        # Check if geist already exists
        if name in state["geists"]:
            print(f"Error: Geist {name} already exists")
            sys.exit(1)

        try:
            # Read personality file
            personality_content = Path(personality_file).read_text()

            # Create container with API key
            container = self.client.containers.run(
                SWARM_IMAGE,
                command="tail -f /dev/null",
                detach=True,
                tty=True,
                stdin_open=True,
                name=f"{CONTAINER_PREFIX}-{name[1:]}",
                working_dir="/workspace",
                environment={
                    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY")
                },
                volumes={SHARED_VOLUME: {'bind': '/shared', 'mode': 'rw'}}
            )

            # Write personality file into container
            container.exec_run(["mkdir", "-p", "/workspace"])
            container.exec_run(
                cmd=["bash", "-c", f"cat > /workspace/personality.txt << 'EOF'\n{personality_content}\nEOF"]
            )

            # Save geist state
            state["geists"][name] = {
                "container_id": container.id[:12],
                "container_name": container.name,
                "personality_file": personality_file,
                "created_at": datetime.utcnow().isoformat() + "Z"
            }
            self.save_state(state)

            print(f"✓ Created geist: {name}")
            print(f"  Container: {container.name} ({container.id[:12]})")

        except docker.errors.APIError as e:
            print(f"Error creating geist: {e}")
            sys.exit(1)

    def list_geists(self):
        """List all geists"""
        # Auto-create default geists if none exist
        self.ensure_default_geists()

        state = self.load_state()

        if not state["geists"]:
            print("No geists found. Create one with:")
            print("  uv run geist create <name> <personality-file>")
            return

        print(f"\n{'NAME':<20} {'CONTAINER ID':<15} {'STATUS':<15}")
        print("-" * 50)

        for name, info in state["geists"].items():
            try:
                container = self.client.containers.get(info["container_id"])
                status = container.status
            except docker.errors.NotFound:
                status = "not found"

            print(f"{name:<20} {info['container_id']:<15} {status:<15}")

        print()

    def get_geist_container(self, name):
        """Get container for a geist by name"""
        if not name.startswith("@"):
            name = f"@{name}"

        state = self.load_state()

        if name not in state["geists"]:
            raise ValueError(f"Geist {name} not found")

        info = state["geists"][name]
        try:
            container = self.client.containers.get(info["container_id"])
            if container.status != 'running':
                container.start()
                time.sleep(1)  # Give it a moment to start
            return container
        except docker.errors.NotFound:
            raise ValueError(f"Container for {name} not found")

    def ask_geist(self, name, question, context=""):
        """Ask a specific geist a question using Claude Code"""
        container = self.get_geist_container(name)

        # Build the prompt for Claude
        prompt = f"""You are {name}, embodying the personality and perspective described in your personality file at /workspace/personality.txt.

{context}

Question: {question}

Respond as {name} would, staying true to their philosophy and communication style."""

        # Execute Claude Code command in container
        # Claude is installed in ~/.local/bin
        # Use --print for non-interactive output
        # Escape single quotes in prompt
        escaped_prompt = prompt.replace("'", "'\\''")
        result = container.exec_run(
            cmd=["bash", "-c", f"echo '{escaped_prompt}' | ~/.local/bin/claude --print"],
            environment={"ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY")}
        )

        # Decode output
        output = result.output.decode('utf-8', errors='ignore').strip()

        # Print debug info
        print(f"[DEBUG {name}] Exit code: {result.exit_code}")
        print(f"[DEBUG {name}] Output length: {len(output)} chars")
        if result.exit_code != 0:
            print(f"[DEBUG {name}] Full error output:\n{output}")

        if result.exit_code != 0:
            return {
                "role": "assistant",
                "name": name,
                "content": f"[Error exit code {result.exit_code}]\n{output}",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

        response = output

        return {
            "role": "assistant",
            "name": name,
            "content": response,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def ask(self, question, geist_names=None):
        """Structured debate format - random order, then rebuttals"""
        import random

        # Auto-create default geists if none exist
        self.ensure_default_geists()

        state = self.load_state()

        # If no geists specified, use all
        if not geist_names:
            geist_names = list(state["geists"].keys())
        else:
            # Ensure @ prefix
            geist_names = [f"@{n}" if not n.startswith("@") else n for n in geist_names]

        if not geist_names:
            print("No geists available. Create some first.")
            return

        # Randomize order for fairness
        random.shuffle(geist_names)

        print(f"\n{'='*80}")
        print(f"QUESTION: {question}")
        print(f"{'='*80}")
        print(f"Participants: {', '.join(geist_names)}")
        print(f"Speaking order: {' → '.join(geist_names)}")
        print(f"{'='*80}\n")

        debate_log = []

        # ROUND 1: Initial Responses
        print("=== ROUND 1: Initial Responses ===\n")

        initial_responses = []
        for geist_name in geist_names:
            context = f"You are participating in a discussion with other geists.\n\nQuestion: {question}\n\nYou are speaking first/early in the order. Provide your perspective."

            print(f"{geist_name}:")
            print("-" * 80)
            response = self.ask_geist(geist_name, question, context)
            print(response['content'])
            print()

            initial_responses.append(response)
            debate_log.append(response)

        # ROUND 2: Rebuttals
        print("\n=== ROUND 2: Rebuttals ===\n")

        for geist_name in geist_names:
            # Build context with all previous responses except their own
            context = f"You are participating in a discussion.\n\nOriginal question: {question}\n\n"
            context += "Other participants have responded:\n\n"

            for resp in initial_responses:
                if resp['name'] != geist_name:
                    # Include full response for rebuttal
                    context += f"{resp['name']}:\n{resp['content']}\n\n"

            context += f"\nNow provide your rebuttal. Address specific points made by others, challenge or build on their arguments."

            rebuttal_question = f"Respond to the other geists' perspectives on: {question}"

            print(f"{geist_name} - Rebuttal:")
            print("-" * 80)
            rebuttal = self.ask_geist(geist_name, rebuttal_question, context)
            print(rebuttal['content'])
            print()

            debate_log.append(rebuttal)

        # Save conversation (both JSON and Markdown)
        self.save_conversation(debate_log)
        md_file = self.save_conversation_as_markdown(question, debate_log, geist_names)

        print("\n" + "=" * 80)
        print(f"Discussion concluded and saved to: {md_file}")
        print("=" * 80)

    def converse(self, topic, rounds=2, geist_names=None):
        """Multi-round conversation between geists"""
        state = self.load_state()

        if not geist_names:
            geist_names = list(state["geists"].keys())
        else:
            geist_names = [f"@{n}" if not n.startswith("@") else n for n in geist_names]

        if len(geist_names) < 2:
            print("Need at least 2 geists for a conversation")
            return

        print(f"\nConversation: {', '.join(geist_names)}")
        print(f"Topic: {topic}")
        print(f"Rounds: {rounds}")
        print("\n" + "=" * 80 + "\n")

        conversation = []
        context = f"Topic: {topic}\n\n"

        for round_num in range(rounds):
            print(f"--- Round {round_num + 1} ---\n")

            for geist_name in geist_names:
                # Build context from previous messages
                if conversation:
                    context = f"Topic: {topic}\n\nPrevious exchanges:\n"
                    for msg in conversation[-5:]:  # Last 5 messages
                        if msg['role'] == 'assistant':
                            context += f"{msg['name']}: {msg['content'][:200]}...\n\n"

                question = f"Share your perspective on: {topic}"
                if round_num > 0:
                    question = f"Respond to the ongoing conversation about: {topic}"

                print(f"{geist_name}:")
                print("-" * 80)
                response = self.ask_geist(geist_name, question, context)
                print(response['content'])
                print()

                conversation.append(response)

        self.save_conversation(conversation)
        print("\n" + "=" * 80)
        print("Conversation saved.")

    def debate(self, topic, affirmative, negative, rounds=3):
        """Structured debate between two geists"""
        # Ensure @ prefix
        if not affirmative.startswith("@"):
            affirmative = f"@{affirmative}"
        if not negative.startswith("@"):
            negative = f"@{negative}"

        state = self.load_state()

        # Validate geists exist
        if affirmative not in state["geists"]:
            print(f"Error: Geist {affirmative} not found")
            sys.exit(1)
        if negative not in state["geists"]:
            print(f"Error: Geist {negative} not found")
            sys.exit(1)

        print(f"\n{'='*80}")
        print(f"DEBATE: {topic}")
        print(f"{'='*80}")
        print(f"AFFIRMATIVE (Pro): {affirmative}")
        print(f"NEGATIVE (Con): {negative}")
        print(f"Rounds: {rounds}")
        print(f"{'='*80}\n")

        debate_log = []

        # Round 1: Opening statements
        print("=== ROUND 1: Opening Statements ===\n")

        # Affirmative opening
        context = f"You are participating in a formal debate.\n\nTopic: {topic}\n\nYou are arguing FOR the affirmative position (supporting the proposition)."
        question = f"Present your opening statement arguing that: {topic}"

        print(f"{affirmative} (PRO) - Opening Statement:")
        print("-" * 80)
        aff_opening = self.ask_geist(affirmative, question, context)
        print(aff_opening['content'])
        print()
        debate_log.append(aff_opening)

        # Negative opening
        context = f"You are participating in a formal debate.\n\nTopic: {topic}\n\nYou are arguing AGAINST the affirmative position (opposing the proposition)."
        question = f"Present your opening statement arguing that: {topic} is FALSE or MISGUIDED"

        print(f"{negative} (CON) - Opening Statement:")
        print("-" * 80)
        neg_opening = self.ask_geist(negative, question, context)
        print(neg_opening['content'])
        print()
        debate_log.append(neg_opening)

        # Middle rounds: Rebuttals
        for round_num in range(2, rounds + 1):
            print(f"\n=== ROUND {round_num}: Rebuttals ===\n")

            # Build context with previous statements
            context_aff = f"You are participating in a formal debate.\n\nTopic: {topic}\n\nYou are arguing FOR the affirmative position.\n\n"
            context_aff += f"Your opponent {negative} argued:\n{neg_opening['content'][:500]}...\n\n"
            if len(debate_log) > 2:
                context_aff += f"Previous exchanges:\n"
                for msg in debate_log[-4:]:
                    context_aff += f"{msg['name']}: {msg['content'][:200]}...\n\n"

            question_aff = f"Rebut your opponent's arguments and strengthen your position that: {topic}"

            print(f"{affirmative} (PRO) - Rebuttal:")
            print("-" * 80)
            aff_rebuttal = self.ask_geist(affirmative, question_aff, context_aff)
            print(aff_rebuttal['content'])
            print()
            debate_log.append(aff_rebuttal)

            # Negative rebuttal
            context_neg = f"You are participating in a formal debate.\n\nTopic: {topic}\n\nYou are arguing AGAINST the affirmative position.\n\n"
            context_neg += f"Your opponent {affirmative} argued:\n{aff_opening['content'][:500]}...\n\n"
            if len(debate_log) > 2:
                context_neg += f"Previous exchanges:\n"
                for msg in debate_log[-4:]:
                    context_neg += f"{msg['name']}: {msg['content'][:200]}...\n\n"

            question_neg = f"Rebut your opponent's arguments and strengthen your position against: {topic}"

            print(f"{negative} (CON) - Rebuttal:")
            print("-" * 80)
            neg_rebuttal = self.ask_geist(negative, question_neg, context_neg)
            print(neg_rebuttal['content'])
            print()
            debate_log.append(neg_rebuttal)

        # Final round: Closing statements
        print(f"\n=== CLOSING STATEMENTS ===\n")

        # Affirmative closing
        context_closing_aff = f"You are giving your FINAL closing statement in this debate.\n\nTopic: {topic}\n\nSummarize your strongest arguments FOR the proposition."
        question_closing_aff = "Present your closing statement, summarizing why your position is correct."

        print(f"{affirmative} (PRO) - Closing Statement:")
        print("-" * 80)
        aff_closing = self.ask_geist(affirmative, question_closing_aff, context_closing_aff)
        print(aff_closing['content'])
        print()
        debate_log.append(aff_closing)

        # Negative closing
        context_closing_neg = f"You are giving your FINAL closing statement in this debate.\n\nTopic: {topic}\n\nSummarize your strongest arguments AGAINST the proposition."
        question_closing_neg = "Present your closing statement, summarizing why your opponent's position is wrong."

        print(f"{negative} (CON) - Closing Statement:")
        print("-" * 80)
        neg_closing = self.ask_geist(negative, question_closing_neg, context_closing_neg)
        print(neg_closing['content'])
        print()
        debate_log.append(neg_closing)

        # Save debate
        self.save_conversation(debate_log)

        print("\n" + "=" * 80)
        print("Debate concluded and saved.")
        print("=" * 80)

    def remove_geist(self, name):
        """Remove a geist"""
        if not name.startswith("@"):
            name = f"@{name}"

        state = self.load_state()

        if name not in state["geists"]:
            print(f"Error: Geist {name} not found")
            sys.exit(1)

        info = state["geists"][name]

        try:
            container = self.client.containers.get(info["container_id"])
            container.stop()
            container.remove()
            print(f"✓ Removed container for {name}")
        except docker.errors.NotFound:
            print(f"Warning: Container not found, removing from state anyway")

        del state["geists"][name]
        self.save_state(state)
        print(f"✓ Removed geist: {name}")

    def show_history(self):
        """Show conversation history"""
        if not CONVERSATION_FILE.exists():
            print("No conversation history found.")
            return

        conversations = json.loads(CONVERSATION_FILE.read_text())

        print(f"\nFound {len(conversations)} conversations:\n")

        for i, conv in enumerate(conversations, 1):
            print(f"Conversation {i} - {conv['timestamp']}")
            print("=" * 80)

            for msg in conv['conversation']:
                role = msg.get('role', 'unknown')
                name = msg.get('name', '')
                content = msg.get('content', '')

                if role == 'user':
                    print(f"\nQUESTION: {content}\n")
                else:
                    print(f"{name}:")
                    print("-" * 80)
                    print(content)
                    print()

            print()

    def reset(self):
        """Remove all geists, containers, and state files"""
        state = self.load_state()

        if not state["geists"]:
            print("No geists found to reset.")
            print()
            return

        print(f"This will remove all {len(state['geists'])} geists and their containers.")
        print("State files (.geist_swarm.json) will also be deleted.")
        print()

        # Stop and remove all containers
        removed_count = 0
        for name, info in state["geists"].items():
            try:
                container = self.client.containers.get(info["container_id"])
                container.stop()
                container.remove()
                print(f"✓ Removed container for {name}")
                removed_count += 1
            except docker.errors.NotFound:
                print(f"⚠ Container for {name} not found (already removed)")

        # Remove state file
        if STATE_FILE.exists():
            STATE_FILE.unlink()
            print(f"✓ Removed state file: {STATE_FILE}")

        print()
        print(f"Reset complete. Removed {removed_count} containers.")
        print("Next time you run 'ask' or 'list', geists will be auto-created from examples/")
        print()


def print_usage():
    print(__doc__)


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]
    swarm = GeistSwarm()

    if command == "create":
        if len(sys.argv) < 4:
            print("Error: Name and personality file required")
            print("Usage: geist.py create <name> <personality-file>")
            sys.exit(1)
        swarm.create_geist(sys.argv[2], sys.argv[3])

    elif command == "list":
        swarm.list_geists()

    elif command == "ask":
        if len(sys.argv) < 3:
            print("Error: Question required")
            print("Usage: geist.py ask \"question\" [--geist @name1,@name2]")
            sys.exit(1)

        question = sys.argv[2]
        geist_names = None

        if len(sys.argv) > 3 and sys.argv[3] == "--geist" and len(sys.argv) > 4:
            geist_names = [n.strip() for n in sys.argv[4].split(",")]

        swarm.ask(question, geist_names)

    elif command == "converse":
        if len(sys.argv) < 3:
            print("Error: Topic required")
            print("Usage: geist.py converse \"topic\" [--rounds N] [--geists @a,@b]")
            sys.exit(1)

        topic = sys.argv[2]
        rounds = 2
        geist_names = None

        # Parse optional flags
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--rounds" and i + 1 < len(sys.argv):
                rounds = int(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == "--geists" and i + 1 < len(sys.argv):
                geist_names = [n.strip() for n in sys.argv[i + 1].split(",")]
                i += 2
            else:
                i += 1

        swarm.converse(topic, rounds, geist_names)

    elif command == "debate":
        if len(sys.argv) < 3:
            print("Error: Topic required")
            print("Usage: geist.py debate \"topic\" --for @geist1 --against @geist2 [--rounds N]")
            sys.exit(1)

        topic = sys.argv[2]
        affirmative = None
        negative = None
        rounds = 3

        # Parse flags
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--for" and i + 1 < len(sys.argv):
                affirmative = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--against" and i + 1 < len(sys.argv):
                negative = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--rounds" and i + 1 < len(sys.argv):
                rounds = int(sys.argv[i + 1])
                i += 2
            else:
                i += 1

        if not affirmative or not negative:
            print("Error: Both --for and --against arguments required")
            print("Usage: geist.py debate \"topic\" --for @geist1 --against @geist2 [--rounds N]")
            sys.exit(1)

        swarm.debate(topic, affirmative, negative, rounds)

    elif command == "remove":
        if len(sys.argv) < 3:
            print("Error: Geist name required")
            print("Usage: geist.py remove <name>")
            sys.exit(1)
        swarm.remove_geist(sys.argv[2])

    elif command == "history":
        swarm.show_history()

    elif command == "reset":
        swarm.reset()

    else:
        print(f"Error: Unknown command '{command}'")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
