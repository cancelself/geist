# Docker Runner

A Python script for managing Docker containers with git and Claude Code pre-installed. This tool allows you to create isolated development environments, execute commands in them, and maintain state between calls.

## Features

- Create new Docker containers with git and Claude Code
- Execute commands in running containers
- Maintain container state between script calls
- Connect to existing containers by ID
- List all running containers
- Attach to containers for interactive sessions
- View container logs

## Prerequisites

- Docker installed and running
- Python 3.6+
- Docker Python SDK (install via `pip install -r requirements.txt`)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure Docker is running:
```bash
docker ps
```

## Usage

### Create a New Container

Create a new container and optionally run a command:

```bash
python docker_runner.py new "git --version"
```

This will:
- Build the Docker image (if not already built)
- Create a new container
- Execute the provided command
- Display the container ID for future reference

### Execute Command in Existing Container

Run a command in an existing container by ID:

```bash
python docker_runner.py exec <container-id> "ls -la"
```

You can use either the full container ID or just the first few characters (e.g., `abc123`).

### List All Containers

View all containers created by this script:

```bash
python docker_runner.py list
```

Example output:
```
ID              NAME                           STATUS          IMAGE
abc123def456    geist-container-a1b2c3d4      running         geist-runner
```

### Attach to Container

Attach to a running container for an interactive session:

```bash
python docker_runner.py attach <container-id>
```

To detach without stopping the container, press `Ctrl+P` then `Ctrl+Q`.

### View Container Logs

Display the logs from a container:

```bash
python docker_runner.py logs <container-id>
```

### Stop a Container

Stop a running container:

```bash
python docker_runner.py stop <container-id>
```

Note: Containers are not automatically deleted when stopped, so you can restart them later.

## Examples

### Example 1: Run a Python script

```bash
# Create new container and run a Python command
python docker_runner.py new "python3 -c 'print(\"Hello from Docker\")'"
```

### Example 2: Clone a git repository

```bash
# Create container and clone a repo
python docker_runner.py new "git clone https://github.com/user/repo.git"

# List containers to get the ID
python docker_runner.py list

# Execute more commands in the same container
python docker_runner.py exec abc123 "cd repo && ls -la"
```

### Example 3: Interactive development session

```bash
# Create a new container
python docker_runner.py new "echo 'Development environment ready'"

# Get the container ID from output
# Container ID: abc123def456

# Attach to the container for interactive work
python docker_runner.py attach abc123

# Inside the container, you can use git, Claude Code, etc.
# Detach with Ctrl+P, Ctrl+Q

# Later, execute more commands
python docker_runner.py exec abc123 "git status"
```

## State Management

The script maintains a state file at `~/.geist_containers.json` that tracks all containers created. This allows you to:

- Resume work in existing containers
- Keep development environments persistent
- Switch between multiple isolated environments

## Container Lifecycle

1. **Create**: New containers are created with a unique ID and kept running
2. **Execute**: Commands can be run in containers at any time
3. **Stop**: Containers can be stopped but remain available
4. **Restart**: Stopped containers automatically restart when you execute commands

Containers persist until you explicitly remove them using Docker commands:
```bash
docker rm <container-id>
```

## Troubleshooting

### Docker connection error
If you see "Could not connect to Docker", ensure:
- Docker Desktop is running (macOS/Windows)
- Docker daemon is running (Linux: `sudo systemctl start docker`)
- Your user has permissions to access Docker

### Image build fails
The script automatically builds the Docker image on first run. If it fails:
- Check your internet connection
- Ensure the Dockerfile is in the same directory
- Try building manually: `docker build -t geist-runner .`

### Container not found
If a container ID is not found:
- Run `python docker_runner.py list` to see all containers
- Use at least the first 4-6 characters of the container ID
- Check that the container hasn't been removed manually

## Architecture

- **Dockerfile**: Defines the container environment with Ubuntu, git, and Claude Code
- **docker_runner.py**: Python script that manages containers using Docker SDK
- **State file**: JSON file tracking container metadata

## Security Notes

- Containers run with default Docker security settings
- No host filesystem is mounted by default
- Each container is isolated from others
- Consider security implications before running untrusted code

## License

Same as the main geist project.
