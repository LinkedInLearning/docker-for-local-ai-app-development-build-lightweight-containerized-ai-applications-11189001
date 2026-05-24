FROM ubuntu:22.04

ARG PYTHON_VER="3.12.11"
ARG RUFF_VER="0.15.12"
ARG VENV_NAME="python-dev"

# Install OS-level dependencies (curl + CA bundle for HTTPS downloads)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install UV and RUFF (Astral installers drop binaries in /root/.local/bin)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
RUN curl -LsSf https://astral.sh/ruff/$RUFF_VER/install.sh | sh

# Make uv/ruff available on PATH for every subsequent RUN and at runtime
ENV PATH="/root/.local/bin:${PATH}"

# Predictable working directory for the rest of the build and at runtime
WORKDIR /app

# Set the Python environment
COPY install_uv.sh requirements.txt settings/
RUN bash ./settings/install_uv.sh $VENV_NAME $PYTHON_VER
