#!/bin/bash
echo "Run Flake8"
./venv/bin/flake8 *.py
echo "Run Black"
./venv/bin/black *.py
echo "Run MyPy"
./venv/bin/mypy *.py