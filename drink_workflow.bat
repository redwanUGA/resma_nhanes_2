@echo off
REM Run a minimal workflow to populate drinking-related CSV files

REM Step 0: Install Python dependencies
python -m pip install -r requirements.txt || goto :error

REM Step 1: Download required NHANES data
python download.py || goto :error

REM Step 2: Generate drinking analysis outputs
python drinker_analysis.py || goto :error

echo Drink workflow completed successfully.
exit /B 0

:error
echo Drink workflow failed.
exit /B 1

