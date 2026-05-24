FROM ubuntu:22.04 

ARG PYTHON_VER="3.12.11"
ARG UV_VER="0.11.16"
ARG RUFF_VER="0.15.12"
ARG VENV_NAME="python-dev"


# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install UV and RUFF
RUN curl -LsSf https://astral.sh/uv/$UV_VER/install.sh | sh
RUN curl -LsSf https://astral.sh/ruff/$RUFF_VER/install.sh | sh

# Set the Python environment
RUN mkdir settings
COPY install_uv.sh requirements.txt settings/
RUN bash ./settings/install_uv.sh $VENV_NAME $PYTHON_VER 
