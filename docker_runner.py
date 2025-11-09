#!/usr/bin/env python3
"""
Docker Runner - Manages Docker containers with git and Claude Code
Usage:
    python docker_runner.py new "command"           - Create new container and run command
    python docker_runner.py exec <id> "command"     - Execute command in existing container
    python docker_runner.py list                     - List all running containers
    python docker_runner.py attach <id>              - Attach to a running container
    python docker_runner.py stop <id>                - Stop a container
    python docker_runner.py logs <id>                - Show container logs
"""

import sys
import json
import docker
import os
from pathlib import Path

IMAGE_NAME = "geist-runner"
CONTAINER_PREFIX = "geist-container"
STATE_FILE = Path.home() / ".geist_containers.json"


class DockerRunner:
    def __init__(self):
        try:
            self.client = docker.from_env()
        except docker.errors.DockerException as e:
            print(f"Error: Could not connect to Docker. Is Docker running?")
            print(f"Details: {e}")
            sys.exit(1)

        self.ensure_image()

    def ensure_image(self):
        """Build the Docker image if it doesn't exist"""
        try:
            self.client.images.get(IMAGE_NAME)
            print(f"Using existing image: {IMAGE_NAME}")
        except docker.errors.ImageNotFound:
            print(f"Building Docker image: {IMAGE_NAME}...")
            dockerfile_dir = Path(__file__).parent
            try:
                self.client.images.build(
                    path=str(dockerfile_dir),
                    tag=IMAGE_NAME,
                    rm=True
                )
                print(f"Successfully built image: {IMAGE_NAME}")
            except docker.errors.BuildError as e:
                print(f"Error building Docker image: {e}")
                sys.exit(1)

    def save_container_state(self, container_id, name):
        """Save container state to file"""
        state = self.load_state()
        state[container_id] = {
            "name": name,
            "id": container_id
        }
        STATE_FILE.write_text(json.dumps(state, indent=2))

    def load_state(self):
        """Load container state from file"""
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
        return {}

    def create_container(self, command=None):
        """Create a new container"""
        try:
            container = self.client.containers.run(
                IMAGE_NAME,
                command="tail -f /dev/null",  # Keep container running
                detach=True,
                tty=True,
                stdin_open=True,
                name=f"{CONTAINER_PREFIX}-{os.urandom(4).hex()}",
                working_dir="/workspace"
            )

            self.save_container_state(container.id[:12], container.name)

            print(f"Created container: {container.name}")
            print(f"Container ID: {container.id[:12]}")

            # Execute initial command if provided
            if command:
                print(f"\nExecuting command: {command}")
                result = container.exec_run(
                    cmd=["bash", "-c", command],
                    tty=True,
                    stream=True
                )

                for chunk in result.output:
                    print(chunk.decode('utf-8', errors='ignore'), end='')

            return container

        except docker.errors.APIError as e:
            print(f"Error creating container: {e}")
            sys.exit(1)

    def get_container(self, container_id):
        """Get a container by ID or name"""
        try:
            # Try exact match first
            return self.client.containers.get(container_id)
        except docker.errors.NotFound:
            # Try prefix match
            containers = self.client.containers.list(all=True)
            for container in containers:
                if container.id.startswith(container_id) or container.name.endswith(container_id):
                    return container
            raise docker.errors.NotFound(f"Container {container_id} not found")

    def exec_command(self, container_id, command):
        """Execute a command in an existing container"""
        try:
            container = self.get_container(container_id)

            # Restart container if it's not running
            if container.status != 'running':
                print(f"Starting stopped container {container.name}...")
                container.start()

            print(f"Executing in {container.name}: {command}")
            result = container.exec_run(
                cmd=["bash", "-c", command],
                tty=True,
                stream=True
            )

            for chunk in result.output:
                print(chunk.decode('utf-8', errors='ignore'), end='')

        except docker.errors.NotFound:
            print(f"Error: Container {container_id} not found")
            sys.exit(1)
        except docker.errors.APIError as e:
            print(f"Error executing command: {e}")
            sys.exit(1)

    def list_containers(self):
        """List all containers created by this script"""
        containers = self.client.containers.list(
            all=True,
            filters={"name": CONTAINER_PREFIX}
        )

        if not containers:
            print("No containers found")
            return

        print(f"{'ID':<15} {'NAME':<30} {'STATUS':<15} {'IMAGE':<20}")
        print("-" * 80)

        for container in containers:
            print(f"{container.id[:12]:<15} {container.name:<30} {container.status:<15} {IMAGE_NAME:<20}")

    def attach_container(self, container_id):
        """Attach to a running container"""
        try:
            container = self.get_container(container_id)

            # Restart container if it's not running
            if container.status != 'running':
                print(f"Starting stopped container {container.name}...")
                container.start()

            print(f"Attaching to {container.name}...")
            print("To detach, press Ctrl+P then Ctrl+Q")
            print("-" * 50)

            # Use os.system to attach with proper TTY
            os.system(f"docker attach {container.id}")

        except docker.errors.NotFound:
            print(f"Error: Container {container_id} not found")
            sys.exit(1)
        except docker.errors.APIError as e:
            print(f"Error attaching to container: {e}")
            sys.exit(1)

    def stop_container(self, container_id):
        """Stop a container"""
        try:
            container = self.get_container(container_id)
            print(f"Stopping {container.name}...")
            container.stop()
            print(f"Container {container.name} stopped")

        except docker.errors.NotFound:
            print(f"Error: Container {container_id} not found")
            sys.exit(1)
        except docker.errors.APIError as e:
            print(f"Error stopping container: {e}")
            sys.exit(1)

    def show_logs(self, container_id):
        """Show container logs"""
        try:
            container = self.get_container(container_id)
            print(f"Logs for {container.name}:")
            print("-" * 50)
            logs = container.logs(tail=100).decode('utf-8', errors='ignore')
            print(logs)

        except docker.errors.NotFound:
            print(f"Error: Container {container_id} not found")
            sys.exit(1)
        except docker.errors.APIError as e:
            print(f"Error fetching logs: {e}")
            sys.exit(1)


def print_usage():
    """Print usage information"""
    print(__doc__)


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]
    runner = DockerRunner()

    if command == "new":
        if len(sys.argv) < 3:
            print("Error: Command required for 'new'")
            print("Usage: docker_runner.py new \"command\"")
            sys.exit(1)
        runner.create_container(sys.argv[2])

    elif command == "exec":
        if len(sys.argv) < 4:
            print("Error: Container ID and command required for 'exec'")
            print("Usage: docker_runner.py exec <id> \"command\"")
            sys.exit(1)
        runner.exec_command(sys.argv[2], sys.argv[3])

    elif command == "list":
        runner.list_containers()

    elif command == "attach":
        if len(sys.argv) < 3:
            print("Error: Container ID required for 'attach'")
            print("Usage: docker_runner.py attach <id>")
            sys.exit(1)
        runner.attach_container(sys.argv[2])

    elif command == "stop":
        if len(sys.argv) < 3:
            print("Error: Container ID required for 'stop'")
            print("Usage: docker_runner.py stop <id>")
            sys.exit(1)
        runner.stop_container(sys.argv[2])

    elif command == "logs":
        if len(sys.argv) < 3:
            print("Error: Container ID required for 'logs'")
            print("Usage: docker_runner.py logs <id>")
            sys.exit(1)
        runner.show_logs(sys.argv[2])

    else:
        print(f"Error: Unknown command '{command}'")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
