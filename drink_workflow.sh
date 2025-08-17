#!/usr/bin/env bash
# Run a minimal workflow to populate drinking-related CSV files
set -euo pipefail

# Step 0: Install Python dependencies
python3 -m pip install -r requirements.txt

# Step 1: Download required NHANES data
python3 download.py

# Step 2: Generate drinking analysis outputs
python3 drinker_analysis.py

