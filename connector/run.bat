@echo off
REM ============================================
REM NexusTrade Quick Run Script
REM Run the app without building EXE
REM ============================================

cd /d "%~dp0"

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

REM Quick install if needed
pip show PyQt6 >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt -q
)

echo Starting NexusTrade...
python main.py
