#!/bin/sh

# Always executed uv with --native-tls:
echo "Updating uv to use --native-tls by default..."
echo "alias uv='uv --native-tls'" >> ~/.bashrc

# Create virtual environment:
echo "Creating virtual environment..."
uv venv --allow-existing .venv
echo 'export VIRTUAL_ENV=/home/vscode/workspace/.venv' >> ~/.bashrc
echo 'export PATH=$VIRTUAL_ENV/bin:$PATH' >> ~/.bashrc

# Install dependencies:
echo "Installing dependencies..."
uv --native-tls pip install --no-progress -r ./requirements.txt
uv --native-tls pip install --no-progress --group dev

# Source bashrc to apply changes:
echo "Sourcing bashrc"
. ~/.bashrc