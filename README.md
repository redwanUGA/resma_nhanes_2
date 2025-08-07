# NHANES Inflammation Analysis

This repository provides Python scripts to download and analyze data from the National Health and Nutrition Examination Survey (NHANES). The analysis focuses on inflammation markers such as Neutrophil-to-Lymphocyte Ratio (NLR), Monocyte-to-Lymphocyte Ratio (MLR), Platelet-to-Lymphocyte Ratio (PLR), the Systemic Immune-Inflammation Index (SII), C‑Reactive Protein (CRP) and blood mercury levels in relation to dental amalgam surfaces.
NHANES did not collect dental examination data during the 2005–2006 and 2007–2008 cycles, so these years are skipped in the workflow.
Download outcomes are tracked in `download_log.csv`, and subsequent analyses use only cycles where every required file was retrieved successfully.

## Repository contents

- `download.py` – downloads the required NHANES XPT files for each cycle (1999–2018) and records the outcome of each download in `download_log.csv`.
- `descriptive_stats.py` – merges demographic, dental, complete blood count, CRP and mercury files, computes inflammation markers and exports `combined_dataset.csv`, `summary_statistics.csv` and `demographic_statistics.csv`.
- `analysis.py` – prepares analysis groups and performs t‑tests (including CRP and blood mercury), saving results to `ttest_results.csv`.
- `regression_models.py` – fits cubic spline and logistic regression models for each marker and exports coefficient and p‑value tables to CSV files.
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
   Data files are saved into a directory named `nhanes_data`, and `download_log.csv` notes which files succeeded or failed.

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

## License

This repository does not include a specific license. Consult the NHANES data usage policies when using these scripts.

