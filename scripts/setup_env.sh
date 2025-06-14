#!/usr/bin/env bash
# Simple helper to create a virtual environment, install dependencies,
# and run tests.
set -e
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt -r requirements-dev.txt
pytest -q
