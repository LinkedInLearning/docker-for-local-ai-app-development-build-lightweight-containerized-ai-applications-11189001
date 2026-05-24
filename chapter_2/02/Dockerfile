FROM ubuntu:22.04 

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install UV and RUFF
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
RUN curl -LsSf https://astral.sh/ruff/install.sh | sh

# Set the Python environment
RUN mkdir settings
COPY install_uv.sh requirements.txt settings/
RUN bash ./settings/install_uv.sh python-dev 3.12.11 
