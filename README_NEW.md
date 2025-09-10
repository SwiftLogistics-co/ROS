# Route Optimization API

A simple and clean FastAPI application for optimizing delivery routes based on coordinates using the nearest neighbor algorithm.

## Features

- 🚚 **Route Optimization**: Optimizes delivery routes using nearest neighbor algorithm
- 📍 **Coordinate-based**: Works with latitude and longitude coordinates
- 🌐 **REST API**: Simple HTTP API with JSON requests/responses
- 📊 **Distance Calculation**: Uses Haversine formula for accurate geographic distances
- 🔍 **Input Validation**: Comprehensive request validation and error handling
- 📚 **API Documentation**: Auto-generated docs at `/docs`

## Quick Start

### Prerequisites
- Python 3.7+
- pip

### Installation

1. Install dependencies:
```bash
pip install fastapi uvicorn
```

2. Run the server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### API Documentation
Visit `http://localhost:8000/docs` for interactive API documentation.

## API Endpoint

### POST `/optimize-coordinates`

Optimizes a route for multiple delivery orders based on their coordinates.

**Request Body:**
```json
{
  "response": {
    "status": "success",
    "orders": {
      "order": [
        {
          "order_id": 1,
          "address": "123 Main Street, Colombo 01",
          "coordinate": {
            "lat": 6.9271,
            "lng": 79.8612
          }
        },
        {
          "order_id": 2,
          "address": "456 Galle Road, Mount Lavinia",
          "coordinate": {
            "lat": 6.8389,
            "lng": 79.8653
          }
        }
      ]
    }
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Route optimized successfully",
  "optimization_summary": {
    "total_orders": 2,
    "total_distance_km": 15.23,
    "algorithm_used": "nearest_neighbor"
  },
  "optimized_route": {
    "orders": [
      {
        "order_id": 1,
        "address": "123 Main Street, Colombo 01",
        "coordinate": {
          "lat": 6.9271,
          "lng": 79.8612
        }
      },
      {
        "order_id": 2,
        "address": "456 Galle Road, Mount Lavinia",
        "coordinate": {
          "lat": 6.8389,
          "lng": 79.8653
        }
      }
    ]
  }
}
```

## Testing

Run the test script:
```bash
python test_api.py
```

## Example Usage with curl

```bash
curl -X POST "http://localhost:8000/optimize-coordinates" \
  -H "Content-Type: application/json" \
  -d '{
    "response": {
      "status": "success",
      "orders": {
        "order": [
          {
            "order_id": 1,
            "address": "123 Main Street, Colombo 01",
            "coordinate": {
              "lat": 6.9271,
              "lng": 79.8612
            }
          },
          {
            "order_id": 2,
            "address": "456 Galle Road, Mount Lavinia",
            "coordinate": {
              "lat": 6.8389,
              "lng": 79.8653
            }
          }
        ]
      }
    }
  }'
```

## Algorithm

The API uses the **Nearest Neighbor Algorithm** for route optimization:

1. Start from the first order in the list
2. Find the nearest unvisited order based on geographic distance
3. Move to that order and repeat until all orders are visited
4. Calculate the total distance using the Haversine formula

## Health Check

- `GET /health` - Returns API health status
- `GET /` - Returns API information and available endpoints

## Docker Support

To run with Docker:

1. Create a Dockerfile:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY main.py .
RUN pip install fastapi uvicorn

CMD ["python", "main.py"]
```

2. Build and run:
```bash
docker build -t route-optimizer .
docker run -p 8000:8000 route-optimizer
```

## Contributing

This is a clean, minimal implementation focusing only on coordinate-based route optimization. The codebase is intentionally simple and easy to understand.
