#!/bin/bash

# ROS Pipeline Development Setup Script
echo "Setting up ROS (Route Optimization System) Pipeline..."

# Create virtual environment
echo "Creating Python virtual environment..."
python -m venv venv

# Activate virtual environment (Linux/Mac)
source venv/bin/activate

# For Windows, use: venv\Scripts\activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

# Set up database (requires PostgreSQL)
echo "Setting up database..."
echo "Make sure PostgreSQL is running and create database:"
echo "CREATE DATABASE ros_db;"
echo "CREATE USER ros_user WITH PASSWORD 'ros_password';"
echo "GRANT ALL PRIVILEGES ON DATABASE ros_db TO ros_user;"

# Optional: Start external services with Docker
echo "Starting external services (optional)..."

# Start OSRM (if Docker is available)
if command -v docker &> /dev/null; then
    echo "Docker found. Starting OSRM server..."
    # Download sample data (Berlin)
    if [ ! -f berlin-latest.osm.pbf ]; then
        wget http://download.geofabrik.de/europe/germany/berlin-latest.osm.pbf
    fi
    
    # Process data
    docker run -t -v "${PWD}:/data" osrm/osrm-backend osrm-extract -p /opt/car.lua /data/berlin-latest.osm.pbf
    docker run -t -v "${PWD}:/data" osrm/osrm-backend osrm-partition /data/berlin-latest.osrm
    docker run -t -v "${PWD}:/data" osrm/osrm-backend osrm-customize /data/berlin-latest.osrm
    
    # Start OSRM server in background
    docker run -d --name ros-osrm -p 5000:5000 -v "${PWD}:/data" osrm/osrm-backend osrm-routed --algorithm mld /data/berlin-latest.osrm
    
    # Start VROOM server
    docker run -d --name ros-vroom -p 3000:3000 vroomvrp/vroom-docker:v1.13.0
    
    echo "OSRM running on http://localhost:5000"
    echo "VROOM running on http://localhost:3000"
else
    echo "Docker not found. Please install Docker to run OSRM and VROOM services."
    echo "Or use the public services (limited rate)"
fi

echo "Setup complete!"
echo ""
echo "To start the ROS API server:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run: uvicorn app.main:app --reload"
echo "3. Open: http://localhost:8000/docs"
echo ""
echo "External services status:"
echo "- Nominatim: Using public service (https://nominatim.openstreetmap.org)"
echo "- OSRM: http://localhost:5000 (if Docker setup completed)"
echo "- VROOM: http://localhost:3000 (if Docker setup completed)"
