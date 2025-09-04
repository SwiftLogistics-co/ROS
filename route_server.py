from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import os
import uvicorn

# Supabase integration (optional)
try:
    from supabase import create_client, Client
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
except ImportError:
    supabase = None
    print("Supabase not available - running without database integration")

app = FastAPI(
    title="Route Optimization System",
    version="1.0.0",
    description="Driver-based route optimization API with Supabase integration",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class OrderLocation(BaseModel):
    order_id: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    priority: Optional[int] = 1

class RouteOptimizationRequest(BaseModel):
    driver_id: int
    start_location: str
    end_location: str
    order_locations: List[OrderLocation]
    route_name: Optional[str] = None

class RouteStop(BaseModel):
    sequence: int
    order_id: str
    location: str
    latitude: float
    longitude: float
    distance_from_previous_km: float
    estimated_travel_time_minutes: int

# Route Optimizer
class RouteOptimizer:
    def __init__(self):
        self.geocoder = Nominatim(user_agent="ROS_API", timeout=10)
    
    def geocode_address(self, address: str) -> tuple:
        try:
            location = self.geocoder.geocode(address)
            if location:
                return location.latitude, location.longitude
            return None, None
        except Exception as e:
            print(f"Geocoding error for {address}: {e}")
            return None, None
    
    def optimize_route(self, request: RouteOptimizationRequest) -> Dict:
        # Geocode start location
        start_lat, start_lon = self.geocode_address(request.start_location)
        if not start_lat or not start_lon:
            raise ValueError(f"Could not geocode start location: {request.start_location}")
        
        # Geocode end location
        end_lat, end_lon = self.geocode_address(request.end_location)
        if not end_lat or not end_lon:
            raise ValueError(f"Could not geocode end location: {request.end_location}")
        
        # Geocode order locations
        valid_locations = []
        for order in request.order_locations:
            if order.latitude and order.longitude:
                valid_locations.append(order)
            else:
                lat, lon = self.geocode_address(order.location)
                if lat and lon:
                    order.latitude = lat
                    order.longitude = lon
                    valid_locations.append(order)
                else:
                    print(f"Warning: Could not geocode order {order.order_id} at {order.location}")
        
        if not valid_locations:
            raise ValueError("No valid order locations found after geocoding")
        
        # Sort by priority
        valid_locations.sort(key=lambda x: x.priority or 1)
        
        # Optimize using nearest neighbor
        current_pos = (start_lat, start_lon)
        unvisited = valid_locations.copy()
        optimized_stops = []
        total_distance = 0.0
        total_time = 0
        sequence = 1
        
        while unvisited:
            nearest_order = None
            min_distance = float('inf')
            
            for order in unvisited:
                distance = geodesic(current_pos, (order.latitude, order.longitude)).kilometers
                if distance < min_distance:
                    min_distance = distance
                    nearest_order = order
            
            travel_time = max(int(min_distance * 2.5), 5)
            
            optimized_stops.append(RouteStop(
                sequence=sequence,
                order_id=nearest_order.order_id,
                location=nearest_order.location,
                latitude=nearest_order.latitude,
                longitude=nearest_order.longitude,
                distance_from_previous_km=round(min_distance, 2),
                estimated_travel_time_minutes=travel_time
            ))
            
            total_distance += min_distance
            total_time += travel_time + 10
            sequence += 1
            current_pos = (nearest_order.latitude, nearest_order.longitude)
            unvisited.remove(nearest_order)
        
        # Add final distance to end location
        final_distance = geodesic(current_pos, (end_lat, end_lon)).kilometers
        total_distance += final_distance
        total_time += max(int(final_distance * 2.5), 5)
        
        route_name = request.route_name or f"Driver_{request.driver_id}_Route_{datetime.now().strftime('%H%M%S')}"
        
        return {
            "driver_id": request.driver_id,
            "route_name": route_name,
            "start_location": request.start_location,
            "end_location": request.end_location,
            "total_distance_km": round(total_distance, 2),
            "total_time_minutes": total_time,
            "total_orders": len(optimized_stops),
            "optimized_route": [stop.dict() for stop in optimized_stops]
        }

optimizer = RouteOptimizer()

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "Route Optimization System",
        "status": "running",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    supabase_status = "connected" if supabase else "not configured"
    return {
        "status": "healthy",
        "service": "Route Optimization API",
        "supabase": supabase_status,
        "endpoints": {
            "POST /optimize-driver-route": "Optimize route for driver with order IDs",
            "GET /driver/{driver_id}/routes": "Get all routes for a driver",
            "GET /health": "Health check"
        }
    }

@app.post("/optimize-driver-route")
async def optimize_driver_route(request: RouteOptimizationRequest):
    """
    Optimize route for a specific driver with order IDs and locations
    """
    try:
        if not request.order_locations:
            raise HTTPException(status_code=400, detail="No order locations provided")
        
        if len(request.order_locations) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 orders allowed per route")
        
        # Optimize the route
        result = optimizer.optimize_route(request)
        
        # Save to Supabase if available
        saved_id = None
        if supabase:
            try:
                route_data = {
                    "route_name": result["route_name"],
                    "driver_id": result["driver_id"],
                    "start_location": result["start_location"],
                    "end_location": result["end_location"]
                }
                
                save_result = supabase.table("routes").insert(route_data).execute()
                if save_result.data:
                    saved_id = save_result.data[0]["id"]
                    
            except Exception as e:
                print(f"Failed to save route to Supabase: {e}")
        
        return {
            "status": "success",
            "route_id": saved_id,
            **result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route optimization failed: {str(e)}")

@app.post("/simple-optimize")
async def simple_optimize(
    driver_id: int,
    start_location: str,
    end_location: str,
    orders: List[Dict[str, Any]]
):
    """
    Simple route optimization endpoint
    """
    try:
        order_locations = []
        for order in orders:
            if "order_id" not in order or "location" not in order:
                raise HTTPException(status_code=400, detail="Each order must have 'order_id' and 'location'")
            
            order_locations.append(OrderLocation(
                order_id=order["order_id"],
                location=order["location"],
                priority=order.get("priority", 1)
            ))
        
        request = RouteOptimizationRequest(
            driver_id=driver_id,
            start_location=start_location,
            end_location=end_location,
            order_locations=order_locations
        )
        
        result = optimizer.optimize_route(request)
        
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route optimization failed: {str(e)}")

@app.get("/driver/{driver_id}/routes")
async def get_driver_routes(driver_id: int, limit: int = 10):
    """Get all routes for a specific driver"""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase not configured")
    
    try:
        result = supabase.table("routes").select("*").eq("driver_id", driver_id).order("created_at", desc=True).limit(limit).execute()
        
        return {
            "status": "success",
            "driver_id": driver_id,
            "total_routes": len(result.data),
            "routes": result.data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get driver routes: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Route Optimization API...")
    print("📍 Server: http://localhost:8000")
    print("📚 Documentation: http://localhost:8000/docs")
    print("🩺 Health Check: http://localhost:8000/health")
    print()
    # Use import string format for reload mode to avoid warning
    uvicorn.run("route_server:app", host="127.0.0.1", port=8000, reload=True)
