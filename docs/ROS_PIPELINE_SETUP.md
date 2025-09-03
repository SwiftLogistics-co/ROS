# ROS Pipeline Setup Guide

## Overview

The Route Optimization System (ROS) Pipeline consists of three main steps:

1. **Geocoding**: Convert literal addresses to coordinates using Nominatim
2. **Route Optimization**: Use VROOM with OSRM for efficient route calculation
3. **Result Processing**: Return optimized delivery routes

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Your App      │───▶│   ROS FastAPI    │───▶│   Optimized     │
│  (Addresses)    │    │    Pipeline      │    │    Routes       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │      Step 1             │
                    │   Nominatim Geocoding   │
                    │   (Addresses → Coords)  │
                    └─────────────────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │      Step 2             │
                    │   VROOM + OSRM          │
                    │   (Route Optimization)  │
                    └─────────────────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │      Step 3             │
                    │   Results Processing    │
                    │   (Formatted Routes)    │
                    └─────────────────────────┘
```

## Step 1: Geocoding with Nominatim

### Built-in Nominatim (Default)
The ROS system uses the public Nominatim service by default:
- No setup required
- Rate limited (1 request/second)
- Suitable for development and small-scale usage

### Self-hosted Nominatim (Production)
For production environments, set up your own Nominatim instance:

```bash
# Using Docker
docker run -it -p 8080:8080 \
  -e PBF_URL=https://download.geofabrik.de/north-america/us-latest.osm.pbf \
  mediagis/nominatim:4.2
```

Update your `.env` file:
```
NOMINATIM_URL=http://localhost:8080
```

## Step 2: VROOM + OSRM Setup

### OSRM Backend Setup

1. **Download map data**:
```bash
# Download map data for your region
wget http://download.geofabrik.de/north-america/us-latest.osm.pbf
```

2. **Process the data**:
```bash
# Extract, partition, and customize
docker run -t -v "${PWD}:/data" osrm/osrm-backend osrm-extract -p /opt/car.lua /data/us-latest.osm.pbf
docker run -t -v "${PWD}:/data" osrm/osrm-backend osrm-partition /data/us-latest.osrm
docker run -t -v "${PWD}:/data" osrm/osrm-backend osrm-customize /data/us-latest.osrm
```

3. **Start OSRM server**:
```bash
docker run -t -i -p 5000:5000 -v "${PWD}:/data" osrm/osrm-backend osrm-routed --algorithm mld /data/us-latest.osrm
```

### VROOM Setup

1. **Install VROOM**:
```bash
# Using Docker
docker pull vroomvrp/vroom-docker:v1.13.0

# Start VROOM server
docker run --rm -it -p 3000:3000 vroomvrp/vroom-docker:v1.13.0
```

2. **Update configuration**:
Edit `.env`:
```
VROOM_URL=http://localhost:3000
OSRM_URL=http://localhost:5000
```

## Step 3: ROS API Usage

### Basic Route Optimization

```python
import requests

# Add vehicles
vehicle_data = {
    "name": "Delivery Van 1",
    "vehicle_type": "van",
    "capacity": 1000,
    "max_distance": 200,
    "cost_per_km": 0.5,
    "start_location": "123 Main St, City, State"
}
response = requests.post("http://localhost:8000/api/v1/vehicles/", json=vehicle_data)
vehicle_id = response.json()["id"]

# Add delivery addresses
address_data = {
    "name": "Customer 1",
    "street_address": "456 Oak Ave",
    "city": "Springfield",
    "state": "IL",
    "postal_code": "62701",
    "country": "USA",
    "delivery_weight": 10,
    "delivery_volume": 5,
    "service_time": 15,
    "priority": 2
}
response = requests.post("http://localhost:8000/api/v1/addresses/", json=address_data)
address_id = response.json()["id"]

# Optimize routes using ROS pipeline
optimization_request = {
    "vehicle_ids": [vehicle_id],
    "address_ids": [address_id],
    "optimization_type": "distance"
}
response = requests.post(
    "http://localhost:8000/api/v1/ros/optimize-advanced", 
    json=optimization_request
)
optimized_routes = response.json()
```

### Batch Geocoding

```python
# Geocode multiple addresses
response = requests.post(
    "http://localhost:8000/api/v1/ros/geocode-batch",
    json=[1, 2, 3, 4, 5]  # Address IDs
)
geocoding_results = response.json()
```

## API Endpoints

### ROS Pipeline Endpoints

- `POST /api/v1/ros/optimize-advanced` - Complete ROS pipeline optimization
- `POST /api/v1/ros/geocode-batch` - Batch geocode addresses

### Standard Endpoints

- `POST /api/v1/vehicles/` - Create vehicle
- `GET /api/v1/vehicles/` - List vehicles
- `POST /api/v1/addresses/` - Create address
- `GET /api/v1/addresses/` - List addresses
- `POST /api/v1/routes/optimize` - Basic route optimization

## Environment Configuration

Create `.env` file from `.env.example`:

```bash
# Core Configuration
DEBUG=True
DATABASE_URL=postgresql://ros_user:ros_password@localhost:5432/ros_db

# ROS Pipeline Configuration
NOMINATIM_URL=https://nominatim.openstreetmap.org
VROOM_URL=http://localhost:3000
OSRM_URL=http://localhost:5000

# Optional: API Keys for enhanced geocoding
GOOGLE_MAPS_API_KEY=your-api-key
MAPBOX_ACCESS_TOKEN=your-token
```

## Performance Optimization

1. **Caching**: The system includes built-in geocoding cache
2. **Batch Processing**: Use batch endpoints for multiple addresses
3. **Database Indexing**: Ensure proper indexes on frequently queried fields
4. **Connection Pooling**: Configure database connection pooling for high load

## Monitoring and Logging

The system includes comprehensive logging for each pipeline step:
- Geocoding success/failure rates
- Route optimization timing
- API response times

## Troubleshooting

### Common Issues

1. **Geocoding Failures**: 
   - Check address format
   - Verify Nominatim service availability
   - Consider using alternative geocoding services

2. **VROOM/OSRM Connection Issues**:
   - Ensure services are running
   - Check network connectivity
   - Verify URL configurations

3. **Performance Issues**:
   - Use self-hosted services for production
   - Implement proper caching strategies
   - Consider geographic data preprocessing

## Production Deployment

For production deployment:

1. Use self-hosted Nominatim and OSRM
2. Set up proper database with connection pooling
3. Configure Redis for caching
4. Use environment-specific configurations
5. Set up monitoring and alerting
6. Implement proper error handling and retries
