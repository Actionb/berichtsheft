FROM mcr.microsoft.com/devcontainers/python:3.13 AS dev

# Install apache2-dev and ca-certificates, and clean up apt cache to reduce image size:
RUN apt update && apt upgrade -y && apt install -y \
    apache2-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Include the CA certificates:
RUN --mount=type=bind,source=../.secrets/ca_certificates.crt,target=/usr/local/share/ca-certificates/ca_certificates.crt update-ca-certificates

# Set the required permissions on the directory created by the named volume for 
# the virtual environment:
RUN mkdir -p /home/vscode/workspace/.venv && \
    chown -R vscode:vscode /home/vscode/workspace/.venv