@echo off
echo GenAI SQL Test Data Generator - API Startup
echo ==========================================

echo.
echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    echo Please run setup.bat first to create the environment
    pause
    exit /b 1
)

echo.
echo [2/3] Installing/updating FastAPI dependencies...
pip install fastapi uvicorn python-multipart aiofiles tabulate --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [3/3] Starting FastAPI server...
echo.
echo API will be available at:
echo - Swagger UI: http://localhost:8000/docs
echo - ReDoc: http://localhost:8000/redoc
echo - Health Check: http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the server
echo.

python start_api.py

pause
