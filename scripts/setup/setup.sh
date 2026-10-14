#!/bin/sh
set -eu
cd "$(dirname "$0")/../.."
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r requirements.lock
