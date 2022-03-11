#!/bin/bash
echo "Run Flake8"
./venv/bin/flake8 ./
echo "Run Black"
./venv/bin/black ./
echo "Run MyPy"
./venv/bin/mypy ./
echo "Running Bandit"
bandit --ini .bandit -rq ${STEP_EXTRA_ARGUMENTS[bandit]} db schemas server.py