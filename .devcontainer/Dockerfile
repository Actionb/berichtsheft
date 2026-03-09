FROM python:3.13-slim-trixie AS dev

RUN apt update && apt upgrade -y && apt install -y \
    apache2-dev \
    ca-certificates \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Include the CA certificates in the build stage to ensure that pip can do its job:
RUN --mount=type=bind,source=../.secrets/ca_certificates.crt,target=/usr/local/share/ca-certificates/ca_certificates.crt update-ca-certificates

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Temporarily mount the requirements:
# https://docs.docker.com/build/building/best-practices/#add-or-copy
RUN --mount=type=bind,source=../requirements.txt,target=/tmp/requirements.txt ["uv", "pip", "install", "--native-tls", "-r", "/tmp/requirements.txt"]

WORKDIR /workspace