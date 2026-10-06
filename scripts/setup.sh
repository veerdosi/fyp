#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r requirements.lock
mkdir -p vendor
if [ ! -d vendor/LIBERO/.git ]; then
  git clone https://github.com/Lifelong-Robot-Learning/LIBERO.git vendor/LIBERO
fi
git -C vendor/LIBERO checkout "$(cat scripts/libero_revision.txt)"
