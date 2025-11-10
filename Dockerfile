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

# Create a non-root user for running Claude Code
RUN useradd -m -s /bin/bash geist && \
    echo "geist ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Switch to non-root user for Claude Code installation
USER geist
WORKDIR /home/geist

# Install Claude Code CLI as non-root user
RUN curl -fsSL https://claude.ai/install.sh | bash

# Create a working directory
WORKDIR /workspace

# Keep container running
CMD ["tail", "-f", "/dev/null"]
