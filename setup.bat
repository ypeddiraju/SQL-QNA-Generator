@echo off
echo GenAI SQL Test Data Generator - Setup Script
echo ============================================

echo.
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)
python --version

echo.
echo [2/4] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
)

echo.
echo [3/4] Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [4/4] Setting up configuration...
if exist .env (
    echo Configuration file .env already exists
) else (
    copy .env.template .env >nul
    echo Configuration template copied to .env
    echo Please edit .env file with your actual credentials
)

echo.
echo ============================================
echo Setup completed successfully!
echo ============================================
echo.
echo Next steps:
echo 1. Edit .env file with your database credentials and OpenAI API key
echo 2. Activate virtual environment: venv\Scripts\activate
echo 3. Run the generator: python generate_dataset.py --tables "Table1,Table2"
echo.
echo For help: python generate_dataset.py --help
echo.

pause
