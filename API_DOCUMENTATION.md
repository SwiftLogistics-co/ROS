# Route Optimization API with Supabase

A simple, fast API for optimizing delivery routes using driver IDs, order IDs, and locations with Supabase as the database backend.

## 🚀 Quick Start

### 1. Set up Supabase
1. Create a new project at [supabase.com](https://supabase.com)
2. Your existing `routes` table structure is perfect!
3. Copy your project URL and anon key

### 2. Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Supabase credentials:
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Start the Server
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: **http://localhost:8000**

## 📡 API Endpoints

### Driver Route Optimization (Main Endpoint)
**POST** `/api/v1/api/optimize-driver-route`

Optimize route for a specific driver with order IDs and locations:

```json
{
  "driver_id": 1,
  "start_location": "Colombo Fort",
  "end_location": "Nugegoda",
  "order_locations": [
    {
      "order_id": "ORD001",
      "location": "Galle Road, Colombo 03",
      "priority": 1
    },
    {
      "order_id": "ORD002", 
      "location": "Kandy Road, Colombo 07",
      "priority": 2
    }
  ],
  "route_name": "Colombo City Express"
}
```

**Response:**
```json
{
  "status": "success",
  "route_id": 15,
  "driver_id": 1,
  "route_name": "Colombo City Express",
  "start_location": "Colombo Fort",
  "end_location": "Nugegoda",
  "total_distance_km": 25.4,
  "total_time_minutes": 75,
  "total_orders": 2,
  "optimized_route": [
    {
      "sequence": 1,
      "order_id": "ORD001",
      "location": "Galle Road, Colombo 03",
      "latitude": 6.9271,
      "longitude": 79.8612,
      "distance_from_previous_km": 3.2,
      "estimated_travel_time_minutes": 8
    }
  ]
}
```

### Get Driver Routes
**GET** `/api/v1/api/driver/{driver_id}/routes`

Get all routes for a specific driver:

```json
{
  "status": "success",
  "driver_id": 1,
  "total_routes": 5,
  "routes": [
    {
      "id": 15,
      "route_name": "Colombo City Express",
      "driver_id": 1,
      "start_location": "Colombo Fort",
      "end_location": "Nugegoda",
      "created_at": "2025-09-03T14:25:30.123Z"
    }
  ]
}
```

### Get Route by ID
**GET** `/api/v1/api/route/{route_id}`

Retrieve a specific route from your routes table.

### List All Routes
**GET** `/api/v1/api/routes?limit=10&driver_id=1`

Get a list of recent routes, optionally filtered by driver.

### Health Check
**GET** `/api/v1/api/health`

Check API status and Supabase connection.

## 🧪 Testing

Test the API with the driver optimization test script:

```bash
python test_driver_optimization.py
```

Or test manually with curl:

```bash
curl -X POST "http://localhost:8000/api/v1/api/optimize-driver-route" \
  -H "Content-Type: application/json" \
  -d '{
    "driver_id": 1,
    "start_location": "Colombo Fort",
    "end_location": "Nugegoda",
    "order_locations": [
      {"order_id": "ORD001", "location": "Galle Road, Colombo"}
    ]
  }'
```

## 🗺️ Sri Lankan Context

The API is optimized for Sri Lankan locations and includes:

- **Major Cities**: Colombo, Kandy, Galle, Jaffna, Negombo
- **Common Areas**: Galle Road, Kandy Road, High Level Road
- **Landmarks**: Colombo Fort, Peradeniya University, Temple of the Tooth

## 📋 API Documentation

Visit http://localhost:8000/docs for interactive Swagger documentation.

## 🏗 Architecture

- **FastAPI**: Fast, modern Python web framework
- **Supabase**: PostgreSQL database with real-time features
- **Geopy**: Address geocoding using Nominatim/OpenStreetMap
- **Nearest Neighbor Algorithm**: Simple but effective route optimization

## 📝 Features

✅ **Driver-based Optimization** - Routes tied to specific drivers  
✅ **Order ID Tracking** - Each stop linked to an order ID  
✅ **Address Geocoding** - Converts addresses to coordinates automatically  
✅ **Priority Support** - Handle high/medium/low priority orders  
✅ **Supabase Integration** - Uses your existing routes table  
✅ **Real-time Processing** - Fast response times  
✅ **Sri Lankan Locations** - Optimized for local addresses  

## 🚚 Use Cases

Perfect for:
- Delivery route optimization in Sri Lanka
- Driver assignment and route planning
- Order fulfillment optimization
- Food delivery services
- Logistics and transportation companies

## 📞 Support

The API integrates with your existing Supabase routes table structure and requires no schema changes.

**Port**: 8000  
**Database**: Your existing Supabase routes table  
**Frontend**: None required - pure API
