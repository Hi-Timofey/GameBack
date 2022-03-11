#!/bin/bash
echo "Run Flake8"
./venv/bin/flake8 ./
echo "Run Black"
./venv/bin/black ./
echo "Run MyPy"
./venv/bin/mypy ./