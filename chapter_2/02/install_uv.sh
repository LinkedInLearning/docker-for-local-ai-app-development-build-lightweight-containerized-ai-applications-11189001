#!/usr/bin/env bash
VENV_NAME=$1
PYTHON_VER=$2

# Setting Python virtual environment
source $HOME/.local/bin/env
uv venv /opt/$VENV_NAME --python $PYTHON_VER \
    && export PATH=/opt/$VENV_NAME/bin:$PATH \
    && echo "source /opt/$VENV_NAME/bin/activate" >> ~/.zshrc


source /opt/$VENV_NAME/bin/activate

uv pip install  --no-cache-dir -r ./settings/requirements.txt
