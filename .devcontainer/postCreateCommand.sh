#!/bin/sh

# Always executed uv with --native-tls:
echo "Updating uv to use --native-tls by default..."
echo "alias uv='uv --native-tls'" >> ~/.bashrc

# Create virtual environment:
echo "Creating virtual environment..."
uv venv --clear ~/venv
echo 'export VIRTUAL_ENV=/home/vscode/venv' >> ~/.bashrc
echo 'export PATH=$VIRTUAL_ENV/bin:$PATH' >> ~/.bashrc

# Install dependencies:
echo "Installing dependencies..."
uv --native-tls pip install -r ./requirements.txt --python ~/venv/bin/python
uv --native-tls pip install --group dev --python ~/venv/bin/python

# Source bashrc to apply changes:
echo "Sourcing bashrc"
. ~/.bashrc