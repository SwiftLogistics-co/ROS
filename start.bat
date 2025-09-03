@echo off
echo Starting ROS (Route Optimization System)...

REM Check if virtual environment exists
if not exist venv (
    echo Virtual environment not found. Running setup...
    call setup.bat
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Start external services with Docker Compose (optional)
echo.
echo Starting external services...
docker-compose up -d postgres redis

REM Wait a moment for services to start
timeout /t 5 /nobreak > nul

REM Start the FastAPI application
echo.
echo Starting ROS API server...
echo API will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
