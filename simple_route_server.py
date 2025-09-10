from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import math
from typing import List

app = FastAPI(
    title="Route Optimization System",
    version="1.0.0",
    description="A coordinate-based route optimization service",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def calculate_distance(coord1: dict, coord2: dict) -> float:
    """Calculate distance between two coordinates using Haversine formula"""
    lat1, lon1 = math.radians(coord1['lat']), math.radians(coord1['lng'])
    lat2, lon2 = math.radians(coord2['lat']), math.radians(coord2['lng'])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Earth's radius in kilometers
    
    return c * r


def optimize_coordinate_route(orders: List[dict]) -> List[dict]:
    """Optimize route using nearest neighbor algorithm"""
    if not orders:
        return []
    
    # Start from the first order
    optimized_route = [orders[0]]
    remaining_orders = orders[1:]
    current_location = orders[0]['coordinate']
    
    while remaining_orders:
        # Find the nearest unvisited order
        nearest_order = min(
            remaining_orders,
            key=lambda order: calculate_distance(current_location, order['coordinate'])
        )
        
        optimized_route.append(nearest_order)
        remaining_orders.remove(nearest_order)
        current_location = nearest_order['coordinate']
    
    return optimized_route


def calculate_total_distance(route: List[dict]) -> float:
    """Calculate total distance for the optimized route"""
    if len(route) < 2:
        return 0.0
    
    total_distance = 0.0
    for i in range(len(route) - 1):
        total_distance += calculate_distance(
            route[i]['coordinate'],
            route[i + 1]['coordinate']
        )
    
    return round(total_distance, 2)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Route Optimization API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Route Optimization System"
    }


@app.post("/api/v1/routes/optimize-coordinates")
async def optimize_route_by_coordinates(request: dict):
    """
    Optimize delivery route based on coordinates using nearest neighbor algorithm
    
    Expected JSON body format:
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
                    }
                ]
            }
        }
    }
    """
    try:
        # Validate request data
        if not request:
            raise HTTPException(status_code=400, detail="No JSON data provided")
        
        # Extract orders from nested structure
        if 'response' not in request or 'orders' not in request['response'] or 'order' not in request['response']['orders']:
            raise HTTPException(
                status_code=400, 
                detail="Invalid data structure. Expected nested 'response.orders.order' structure"
            )
        
        orders = request['response']['orders']['order']
        
        if not orders or not isinstance(orders, list):
            raise HTTPException(
                status_code=400, 
                detail="No orders provided or invalid format"
            )
        
        # Validate order structure
        for order in orders:
            if not all(key in order for key in ['order_id', 'address', 'coordinate']):
                raise HTTPException(
                    status_code=400, 
                    detail="Each order must have order_id, address, and coordinate"
                )
            
            if not all(key in order['coordinate'] for key in ['lat', 'lng']):
                raise HTTPException(
                    status_code=400, 
                    detail="Each coordinate must have lat and lng"
                )
        
        # Optimize the route
        optimized_orders = optimize_coordinate_route(orders)
        total_distance = calculate_total_distance(optimized_orders)
        
        # Prepare response
        response = {
            "status": "success",
            "message": "Route optimized successfully",
            "optimization_summary": {
                "total_orders": len(optimized_orders),
                "total_distance_km": total_distance,
                "algorithm_used": "nearest_neighbor"
            },
            "optimized_route": {
                "orders": optimized_orders
            }
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "simple_route_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
