@echo off
setlocal

:: Check input
if "%~1"=="" (
    echo Usage: %~nx0 INPUT_DIR
    exit /b 1
)

set "INPUT_DIR=%~1"

:: Set your conda environment name here
set "CONDA_ENV_NAME=env\webvoyager"

:: Activate conda environment
call conda activate %CONDA_ENV_NAME%
if errorlevel 1 (
    echo Failed to activate Conda environment "%CONDA_ENV_NAME%"
    exit /b 1
)

:: Run the first Python script
python src\ui_test_oh\ui_eval_with_answer.py --in_dir %INPUT_DIR%

pm2 delete all

endlocal
