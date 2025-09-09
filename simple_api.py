"""
SIMPLE ROUTE API
Just fetch coordinates and return optimized route
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Tuple
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import uvicorn

app = FastAPI(title="Simple Route Optimizer API")

# Models
class LocationRequest(BaseModel):
    addresses: List[str]

class CoordinateRequest(BaseModel):
    coordinates: List[Tuple[float, float]]

class RouteResponse(BaseModel):
    optimized_coordinates: List[Tuple[float, float]]
    addresses: List[str] = None
    distances: List[float]
    total_distance: float

# Initialize geocoder
geocoder = Nominatim(user_agent="SimpleRouteAPI", timeout=10)

def get_coordinates(address: str) -> Tuple[float, float]:
    """Get coordinates for address"""
    try:
        location = geocoder.geocode(address)
        if location:
            return (location.latitude, location.longitude)
        else:
            raise ValueError(f"Address not found: {address}")
    except Exception as e:
        raise ValueError(f"Geocoding failed: {e}")

def optimize_route(coordinates: List[Tuple[float, float]]) -> dict:
    """Optimize route using nearest neighbor"""
    if len(coordinates) < 2:
        raise ValueError("Need at least 2 locations")
    
    if len(coordinates) == 2:
        distance = geodesic(coordinates[0], coordinates[1]).kilometers
        return {
            "optimized_coordinates": coordinates,
            "distances": [0, round(distance, 2)],
            "total_distance": round(distance, 2)
        }
    
    # Keep start and end fixed, optimize middle
    start = coordinates[0]
    end = coordinates[-1]
    middle = coordinates[1:-1]
    
    optimized = [start]
    current = start
    remaining = middle[:]
    distances = [0]
    total_distance = 0
    
    # Nearest neighbor optimization
    while remaining:
        nearest_idx = 0
        min_dist = geodesic(current, remaining[0]).kilometers
        
        for i, point in enumerate(remaining[1:], 1):
            dist = geodesic(current, point).kilometers
            if dist < min_dist:
                min_dist = dist
                nearest_idx = i
        
        nearest = remaining.pop(nearest_idx)
        optimized.append(nearest)
        distances.append(round(min_dist, 2))
        total_distance += min_dist
        current = nearest
    
    # Add end point
    final_dist = geodesic(current, end).kilometers
    optimized.append(end)
    distances.append(round(final_dist, 2))
    total_distance += final_dist
    
    return {
        "optimized_coordinates": optimized,
        "distances": distances,
        "total_distance": round(total_distance, 2)
    }

@app.post("/optimize-addresses", response_model=RouteResponse)
async def optimize_from_addresses(request: LocationRequest):
    """
    Input: List of addresses
    Output: Coordinates and optimized route
    """
    try:
        # Get coordinates for all addresses
        coordinates = []
        for address in request.addresses:
            coord = get_coordinates(address)
            coordinates.append(coord)
        
        # Optimize route
        result = optimize_route(coordinates)
        
        return RouteResponse(
            optimized_coordinates=result["optimized_coordinates"],
            addresses=request.addresses,
            distances=result["distances"],
            total_distance=result["total_distance"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/optimize-coordinates", response_model=RouteResponse)
async def optimize_from_coordinates(request: CoordinateRequest):
    """
    Input: List of coordinates 
    Output: Optimized route
    """
    try:
        result = optimize_route(request.coordinates)
        
        return RouteResponse(
            optimized_coordinates=result["optimized_coordinates"],
            distances=result["distances"],
            total_distance=result["total_distance"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/coordinates/{address}")
async def get_address_coordinates(address: str):
    """Get coordinates for a single address"""
    try:
        coord = get_coordinates(address)
        return {
            "address": address,
            "latitude": coord[0],
            "longitude": coord[1]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
async def root():
    return {
        "message": "Simple Route Optimizer API",
        "endpoints": {
            "POST /optimize-addresses": "Optimize route from addresses",
            "POST /optimize-coordinates": "Optimize route from coordinates",
            "GET /coordinates/{address}": "Get coordinates for address"
        },
        "example": {
            "addresses": ["Colombo Fort", "Galle Road, Colombo", "Mount Lavinia"],
            "coordinates": [[6.9338, 79.8501], [6.9146, 79.8486]]
        }
    }

if __name__ == "__main__":
    print("🚀 Starting Simple Route Optimizer API")
    print("📍 http://localhost:8001")
    print("📚 Docs: http://localhost:8001/docs")
    uvicorn.run("simple_api:app", host="127.0.0.1", port=8001, reload=True)
