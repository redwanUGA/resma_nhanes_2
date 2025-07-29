# NHANES Inflammation Analysis

This repository contains Python scripts and a Jupyter notebook used to download and analyze data from the National Health and Nutrition Examination Survey (NHANES). The analysis focuses on inflammation markers such as Neutrophil-to-Lymphocyte Ratio (NLR), Monocyte-to-Lymphocyte Ratio (MLR), Platelet-to-Lymphocyte Ratio (PLR) and the Systemic Immune-Inflammation Index (SII) in relation to dental amalgam surfaces.

## Repository contents

- `download.py` – downloads the required NHANES XPT files for each cycle.
- `descriptive_stats.py` – merges demographic, dental and complete blood count files, computes summary statistics for inflammation markers and exports CSV files.
- `analysis.py` – prepares analysis groups and performs t‑tests (and optional survey‑weighted ANOVA via R).
- `NHANES_HG_OPT.ipynb` – original notebook that demonstrates the workflow.

## Setup

The scripts rely on the following Python packages:

- `pandas`
- `numpy`
- `scipy`
- `pyreadstat`
- `requests`
- `statsmodels` (for survey-weighted ANOVA)

Install the dependencies with `pip`:

```bash
pip install pandas numpy scipy matplotlib pyreadstat requests statsmodels
```

## Usage

1. **Download the NHANES data**

   ```bash
   python download.py
   ```
   Data files are saved into a directory named `nhanes_data`.

2. **Generate descriptive statistics**

   ```bash
   python descriptive_stats.py
   ```
   This produces `combined_dataset.csv` and `summary_statistics.csv`.

3. **Run analyses**

   ```bash
   python analysis.py
   ```
   T‑test results are written to `ttest_results.csv`.

4. **Generate box plots**

   ```bash
   python box_plots.py
   ```
   Figures are saved into the `output` directory.

The notebook `NHANES_HG_OPT.ipynb` can be used to explore or reproduce the workflow interactively.

## License

This repository does not include a specific license. Consult the NHANES data usage policies when using these scripts.

