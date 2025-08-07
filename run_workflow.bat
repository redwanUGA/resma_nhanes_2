@echo off
REM Run the full NHANES inflammation analysis workflow

REM Step 0: Install Python dependencies
python -m pip install -r requirements.txt || goto :error

REM Step 1: Download data
python download.py || goto :error

REM Step 2: Generate descriptive statistics
python descriptive_stats.py || goto :error

REM Step 3: Run t-test analyses
python analysis.py || goto :error

REM Step 4: Run regression models
python regression_models.py || goto :error

echo Workflow completed successfully.
exit /B 0

:error
echo Workflow failed.
exit /B 1
