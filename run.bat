@echo off
REM ASPM Backend Startup Script for Windows

echo Starting ASPM Backend Server...
echo.

REM Check if venv exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate

REM Install requirements if not already installed
pip show fastapi > nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Initialize database if it doesn't exist
if not exist "aspm.db" (
    echo Initializing database...
    python init_db.py
)

echo.
echo Starting FastAPI server on http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.

REM Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
