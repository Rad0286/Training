@echo off
echo ============================================
echo  Case Reference Extractor ^& Highlighter
echo ============================================
echo.

:: Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.11+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/2] Installing / checking dependencies...
pip install -r "%~dp0requirements.txt" --quiet

echo [2/2] Starting the app...
echo.
echo The app will open in your browser at http://localhost:8501
echo Press Ctrl+C in this window to stop the app.
echo.

python -m streamlit run "%~dp0app.py" --server.port=8501 --server.headless=true --browser.serverAddress=localhost

pause