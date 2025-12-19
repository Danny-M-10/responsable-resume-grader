@echo off
REM Recruitment Candidate Ranker - Setup Script (Windows)
REM Installs dependencies and verifies installation

echo ==========================================
echo Recruitment Candidate Ranker Setup
echo ==========================================
echo.

REM Check Python installation
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python version: %PYTHON_VERSION%
echo.

REM Install dependencies
echo Installing dependencies...
echo This may take a few minutes...
echo.

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies
    echo Please try manually: python -m pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Installation Complete!
echo ==========================================
echo.
echo Next Steps:
echo.
echo 1. Launch Web Interface (Recommended):
echo    streamlit run app.py
echo.
echo 2. Or use Python API:
echo    python example_usage.py
echo.
echo 3. Read documentation:
echo    - QUICK_START.md for fast setup
echo    - USER_MANUAL.md for comprehensive guide
echo    - README.md for technical details
echo.
echo ==========================================
echo.
pause
