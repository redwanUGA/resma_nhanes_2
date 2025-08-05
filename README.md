# NHANES Inflammation Analysis

This repository provides Python scripts to download and analyze data from the National Health and Nutrition Examination Survey (NHANES). The analysis focuses on inflammation markers such as Neutrophil-to-Lymphocyte Ratio (NLR), Monocyte-to-Lymphocyte Ratio (MLR), Platelet-to-Lymphocyte Ratio (PLR), the Systemic Immune-Inflammation Index (SII), C‑Reactive Protein (CRP) and blood mercury levels in relation to dental amalgam surfaces.

## Repository contents

- `download.py` – downloads the required NHANES XPT files for each cycle (1999–2018).
- `descriptive_stats.py` – merges demographic, dental, complete blood count, CRP and mercury files, computes inflammation markers and exports `combined_dataset.csv`, `summary_statistics.csv` and `demographic_statistics.csv`.
- `analysis.py` – prepares analysis groups and performs t‑tests (including CRP and blood mercury), saving results to `ttest_results.csv`.
- `regression_models.py` – fits cubic spline and logistic regression models for each marker and exports coefficient and p‑value tables to CSV files.
- `box_plots.py` – reads `ttest_results.csv` and generates box plots for significant comparisons, saving figures to the `output` directory.
- `run_workflow.sh` – runs the entire workflow in one command.

## Setup

The scripts rely on the following Python packages:

- `pandas`
- `numpy`
- `scipy`
- `matplotlib`
- `pyreadstat`
- `requests`
- `statsmodels` (for survey-weighted ANOVA)

All required packages are listed in `requirements.txt`. Install them with:

```bash
pip install -r requirements.txt
```

## Usage

To run every step in sequence, execute:
```bash
./run_workflow.sh
```


1. **Download the NHANES data**

   ```bash
   python download.py
   ```
   Data files are saved into a directory named `nhanes_data`.

2. **Generate descriptive statistics**

   ```bash
   python descriptive_stats.py
   ```
   Produces `combined_dataset.csv`, `summary_statistics.csv` and `demographic_statistics.csv`.

3. **Run t-test analyses**

   ```bash
   python analysis.py
   ```
   Writes t‑test results to `ttest_results.csv`.

4. **Run regression models**

   ```bash
   python regression_models.py
   ```
   Produces cubic spline and logistic regression outputs: `cubic_spline_coeffs.csv`, `cubic_spline_pvalues.csv`, `logistic_coeffs.csv` and `logistic_pvalues.csv`.

5. **Generate box plots**

   ```bash
   python box_plots.py
   ```
   Reads `ttest_results.csv` and saves figures for significant comparisons to the `output` directory.

## License

This repository does not include a specific license. Consult the NHANES data usage policies when using these scripts.

