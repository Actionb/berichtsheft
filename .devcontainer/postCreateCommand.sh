#!/bin/sh

# Create virtual environment:
echo "Creating virtual environment..."
uv venv --allow-existing .venv
echo 'export VIRTUAL_ENV=/home/vscode/workspace/.venv' >> ~/.bashrc
echo 'export PATH=$VIRTUAL_ENV/bin:$PATH' >> ~/.bashrc

# Install dependencies:
echo "Installing dependencies..."
uv --system-certs sync

# Source bashrc to apply changes:
echo "Sourcing bashrc"
. ~/.bashrc