FROM ubuntu:22.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install git, python3, pip, curl and other essentials
RUN apt-get update && apt-get install -y \
    git \
    python3 \
    python3-pip \
    curl \
    wget \
    sudo \
    vim \
    nano \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI
RUN curl -fsSL https://claude.ai/install.sh | sh

# Create a working directory
WORKDIR /workspace

# Keep container running
CMD ["tail", "-f", "/dev/null"]
