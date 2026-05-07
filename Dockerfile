FROM python:3.13-slim-trixie AS build

RUN ["apt", "update"]
RUN ["apt", "install", "-y", "apache2-dev", "ca-certificates"]

# Include any provided CA certificate:
ARG CA_CERT
RUN if [ -n "$CA_CERT" ]; then \
        echo "$CA_CERT" | base64 -d > /usr/local/share/ca-certificates/extra-ca.crt && \
        update-ca-certificates; \
    fi

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv

# Temporarily mount the requirements:
# https://docs.docker.com/build/building/best-practices/#add-or-copy
RUN --mount=type=bind,source=pyproject.toml,target=/tmp/pyproject.toml \
    ["uv", "--native-tls", "pip", "install", "--no-cache-dir", "-r", "/tmp/pyproject.toml"]

FROM python:3.13-slim-trixie AS final

RUN ["apt", "update"]
RUN ["apt", "upgrade", "-y"]
RUN ["apt", "install", "-y", "apache2", "curl"]

COPY --from=build /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /bapp
COPY . /bapp

RUN ["mkdir", "/bapp/media"]
RUN ["chown", "-R", "www-data:www-data", "/bapp/media"]