#!/usr/bin/env bash
# Run the full NHANES inflammation analysis workflow
set -euo pipefail

# Step 1: Download data
python3 download.py

# Step 2: Generate descriptive statistics
python3 descriptive_stats.py

# Step 3: Run analyses
python3 analysis.py

# Step 4: Generate box plots
python3 box_plots.py
