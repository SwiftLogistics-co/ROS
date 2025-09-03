# Route Optimization System (ROS)

A modern, cloud-based Route Optimization System built with FastAPI that takes delivery addresses and vehicle availability to generate the most efficient routes using the practical ROS pipeline.

## 🚀 Features

- **3-Step ROS Pipeline**: 
  1. **Geocoding** with Nominatim (literal addresses → coordinates)
  2. **Route Optimization** with VROOM + OSRM 
  3. **Optimized Results** with efficient delivery routes
- **RESTful API**: Well-documented API endpoints for route optimization
- **Vehicle Management**: Handle multiple vehicle types and constraints
- **Address Optimization**: Intelligent route planning based on delivery addresses
- **Real-time Processing**: Fast route calculation using modern algorithms
- **Scalable Architecture**: Cloud-ready with horizontal scaling capabilities
- **SOAP Support**: Legacy SOAP service compatibility
- **Database Integration**: PostgreSQL for persistent data storage
- **Caching**: Redis for performance optimization
- **Background Tasks**: Celery for asynchronous processing

## 🛠 Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis
- **Background Tasks**: Celery
- **Geocoding**: Nominatim (OSM)
- **Route Optimization**: VROOM + OSRM
- **Documentation**: Automatic OpenAPI/Swagger documentation

## ⚡ Quick Start

### Windows Setup
```cmd
# Clone the repository
git clone https://github.com/SwiftLogistics-co/ROS.git
cd ROS

# Run the setup script
setup.bat

# Start the application
start.bat
```

### Manual Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start external services (optional):
```bash
docker-compose up -d
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

5. Access the API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📋 ROS Pipeline Usage

### Step 1: Add Vehicles and Addresses

```python
import requests

base_url = "http://localhost:8000/api/v1"

# Add a delivery vehicle
vehicle_data = {
    "name": "Delivery Van 1",
    "vehicle_type": "van", 
    "capacity": 1000,
    "max_distance": 200,
    "cost_per_km": 0.5,
    "start_location": "123 Main St, Springfield, IL"
}
vehicle = requests.post(f"{base_url}/vehicles/", json=vehicle_data).json()

# Add delivery addresses
addresses_data = [
    {
        "name": "Customer A",
        "street_address": "456 Oak Ave",
        "city": "Springfield", 
        "state": "IL",
        "postal_code": "62701",
        "country": "USA",
        "delivery_weight": 15,
        "delivery_volume": 8,
        "service_time": 10,
        "priority": 2
    },
    {
        "name": "Customer B",
        "street_address": "789 Pine St", 
        "city": "Springfield",
        "state": "IL", 
        "postal_code": "62702",
        "country": "USA",
        "delivery_weight": 25,
        "delivery_volume": 12,
        "service_time": 15,
        "priority": 1
    }
]

address_ids = []
for addr_data in addresses_data:
    addr = requests.post(f"{base_url}/addresses/", json=addr_data).json()
    address_ids.append(addr["id"])
```

### Step 2: Run ROS Pipeline Optimization

```python
# Run the complete ROS pipeline
optimization_request = {
    "vehicle_ids": [vehicle["id"]],
    "address_ids": address_ids,
    "optimization_type": "distance"
}

response = requests.post(
    f"{base_url}/ros/optimize-advanced",
    json=optimization_request
)

result = response.json()
print(f"✅ Optimization completed!")
print(f"📊 Total Distance: {result['summary']['total_distance_km']} km")
print(f"⏱️  Total Time: {result['summary']['total_time_minutes']} minutes")
print(f"💰 Total Cost: ${result['summary']['total_cost']}")
```

## 🗺️ API Endpoints

### ROS Pipeline Endpoints
- `POST /api/v1/ros/optimize-advanced` - Complete ROS pipeline optimization
- `POST /api/v1/ros/geocode-batch` - Batch geocode addresses

### Vehicle Management
- `POST /api/v1/vehicles` - Add new vehicle
- `GET /api/v1/vehicles` - List all vehicles
- `PUT /api/v1/vehicles/{vehicle_id}` - Update vehicle
- `DELETE /api/v1/vehicles/{vehicle_id}` - Remove vehicle

### Address Management
- `POST /api/v1/addresses` - Add delivery address
- `GET /api/v1/addresses` - List all addresses
- `PUT /api/v1/addresses/{address_id}` - Update address
- `DELETE /api/v1/addresses/{address_id}` - Remove address

### Route Management
- `POST /api/v1/routes/optimize` - Basic route optimization
- `GET /api/v1/routes/{route_id}` - Get optimized route by ID
- `GET /api/v1/routes` - List all routes with pagination

## 🏗 ROS Pipeline Architecture

```
Input: Literal Addresses + Vehicles
         ↓
Step 1: Geocoding (Nominatim)
    📍 "123 Main St" → [40.7128, -74.0060]
         ↓
Step 2: Route Optimization (VROOM + OSRM)  
    🚚 Vehicles + 📍 Coordinates → 🗺️ Routes
         ↓
Step 3: Optimized Results
    📋 Efficient delivery routes with timing
```

## 🐳 External Services Setup

### Option 1: Docker Compose (Recommended)
```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)  
- OSRM (port 5000)
- VROOM (port 3000)
- Nominatim (port 8080) - optional

### Option 2: Individual Services
See [docs/ROS_PIPELINE_SETUP.md](docs/ROS_PIPELINE_SETUP.md) for detailed setup instructions.

## 🧪 Testing

Run the test pipeline:
```bash
python test_ros_pipeline.py
```

## 📚 Documentation

- [ROS Pipeline Setup Guide](docs/ROS_PIPELINE_SETUP.md)
- [API Documentation](http://localhost:8000/docs) (when running)

## 🔧 Configuration

Key environment variables in `.env`:
```env
# Database
DATABASE_URL=postgresql://ros_user:ros_password@localhost:5432/ros_db

# External Services  
VROOM_URL=http://localhost:3000
OSRM_URL=http://localhost:5000
NOMINATIM_URL=http://localhost:8080

# Optional API Keys
GOOGLE_MAPS_API_KEY=your-api-key
MAPBOX_ACCESS_TOKEN=your-token
```

## 🚀 Production Deployment

For production environments:
1. Use self-hosted Nominatim and OSRM services
2. Configure proper database with connection pooling
3. Set up Redis for caching and session management
4. Use environment-specific configurations
5. Implement monitoring and alerting
6. Set up proper error handling and retries

## 📄 License

MIT License
