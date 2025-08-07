#!/usr/bin/env bash
# Run the full NHANES inflammation analysis workflow
set -euo pipefail

# Step 0: Install Python dependencies
python3 -m pip install -r requirements.txt

# Step 1: Download data
python3 download.py

# Step 2: Generate descriptive statistics
python3 descriptive_stats.py

# Step 3: Run t-test analyses
python3 analysis.py

# Step 4: Run regression models
python3 regression_models.py
