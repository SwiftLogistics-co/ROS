@echo off
REM ROS Pipeline Development Setup Script for Windows
echo Setting up ROS (Route Optimization System) Pipeline...

REM Create virtual environment
echo Creating Python virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file...
    copy .env.example .env
    echo Please edit .env file with your configuration
)

REM Set up database instructions
echo.
echo Setting up database...
echo Make sure PostgreSQL is running and create database:
echo CREATE DATABASE ros_db;
echo CREATE USER ros_user WITH PASSWORD 'ros_password';
echo GRANT ALL PRIVILEGES ON DATABASE ros_db TO ros_user;
echo.

REM Check for Docker
docker --version >nul 2>&1
if %errorlevel% == 0 (
    echo Docker found. You can optionally set up OSRM and VROOM services.
    echo See docs/ROS_PIPELINE_SETUP.md for detailed instructions.
) else (
    echo Docker not found. External services will use public APIs.
)

echo.
echo Setup complete!
echo.
echo To start the ROS API server:
echo 1. Make sure virtual environment is activated: venv\Scripts\activate
echo 2. Run: uvicorn app.main:app --reload
echo 3. Open: http://localhost:8000/docs
echo.
echo External services status:
echo - Nominatim: Using public service (https://nominatim.openstreetmap.org)
echo - OSRM: Configure in .env if available
echo - VROOM: Configure in .env if available

pause
