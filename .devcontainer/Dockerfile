FROM mcr.microsoft.com/devcontainers/python:3.13 AS dev

RUN apt update && apt upgrade -y && apt install -y \
    apache2-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Include the CA certificates in the build stage to ensure that pip can do its job:
RUN --mount=type=bind,source=../.secrets/ca_certificates.crt,target=/usr/local/share/ca-certificates/ca_certificates.crt update-ca-certificates