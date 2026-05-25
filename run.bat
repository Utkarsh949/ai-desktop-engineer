@echo off
REM ============================================================================
REM AI Desktop Engineer - One-Click Launcher
REM ============================================================================
REM This script sets up the environment and runs the application with one click

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ╔════════════════════════════════════════════════════════════════════════╗
echo ║        🚀 AI Desktop Engineer - Auto Setup & Launch                    ║
echo ╚════════════════════════════════════════════════════════════════════════╝
echo.

REM ============================================================================
REM Step 1: Check if Python is installed
REM ============================================================================
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python not found! Please install Python 3.10+
    echo 📥 Download from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Found: %PYTHON_VERSION%
echo.

REM ============================================================================
REM Step 2: Create virtual environment if it doesn't exist
REM ============================================================================
echo [2/5] Setting up virtual environment...
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)
echo.

REM ============================================================================
REM Step 3: Activate virtual environment and install requirements
REM ============================================================================
echo [3/5] Installing dependencies...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
echo 📥 Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

REM Install requirements
echo 📥 Installing packages from requirements.txt...
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo ✅ Dependencies installed successfully
echo.

REM ============================================================================
REM Step 4: Check .env file configuration
REM ============================================================================
echo [4/5] Checking configuration...
if not exist ".env" (
    echo ⚠️  WARNING: .env file not found!
    echo 📝 Creating .env file with defaults...
    (
        echo GROQ_API_KEY=
        echo GROQ_MODEL=llama-3.3-70b-versatile
        echo GITHUB_TOKEN=
        echo PROJECTS_DIR=./config/projects
        echo EXPORTS_DIR=./config/exports
        echo MAX_TOKENS=4096
    ) > .env
    echo ✅ Created .env file (configure your API keys!)
) else (
    echo ✅ .env file found
)
echo.

REM ============================================================================
REM Step 5: Launch the application
REM ============================================================================
echo [5/5] Launching AI Desktop Engineer...
echo ✅ Starting application...
echo.
python run.py

REM If application closes, keep window open briefly to see errors
if errorlevel 1 (
    echo.
    echo ❌ Application exited with an error
    pause
)

endlocal
