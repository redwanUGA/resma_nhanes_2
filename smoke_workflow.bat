@echo off
REM Run a minimal workflow to populate smoking-related CSV files

REM Step 0: Install Python dependencies
python -m pip install -r requirements.txt || goto :error

REM Step 1: Download required NHANES data
python download.py || goto :error

REM Step 2: Generate smoking analysis outputs
python smoker_analysis.py || goto :error

echo Smoke workflow completed successfully.
exit /B 0

:error
echo Smoke workflow failed.
exit /B 1
