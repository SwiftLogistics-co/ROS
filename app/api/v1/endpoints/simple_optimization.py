from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import asyncio
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import json

router = APIRouter()

# Simple models for the streamlined API
class LocationRequest(BaseModel):
    order_id: str
    address: str
    latitude: float = None
    longitude: float = None
    priority: int = 1  # 1=high, 2=medium, 3=low
    delivery_time_window: str = None  # e.g., "09:00-17:00"

class VehicleRequest(BaseModel):
    vehicle_id: str
    start_location: str
    start_latitude: float = None
    start_longitude: float = None
    capacity: float = 100.0
    max_distance: float = 200.0

class OptimizationRequest(BaseModel):
    vehicle: VehicleRequest
    locations: List[LocationRequest]
    optimization_type: str = "distance"  # "distance", "time", "balanced"

class RouteStop(BaseModel):
    order_id: str
    address: str
    latitude: float
    longitude: float
    sequence: int
    distance_from_previous: float
    estimated_travel_time: int  # minutes
    priority: int

class OptimizedRoute(BaseModel):
    vehicle_id: str
    total_distance: float  # km
    total_time: int  # minutes
    total_stops: int
    route_stops: List[RouteStop]

class OptimizationResponse(BaseModel):
    status: str
    message: str
    optimized_route: OptimizedRoute

# Simple geocoding service
class SimpleGeocodingService:
    def __init__(self):
        self.geocoder = Nominatim(user_agent="ROS_API")
    
    def geocode_address(self, address: str) -> tuple:
        """Geocode an address to lat/lon"""
        try:
            location = self.geocoder.geocode(address)
            if location:
                return location.latitude, location.longitude
            return None, None
        except Exception as e:
            print(f"Geocoding error for {address}: {e}")
            return None, None

# Simple route optimization service
class SimpleRouteOptimizer:
    def __init__(self):
        self.geocoding_service = SimpleGeocodingService()
    
    def optimize_route(self, request: OptimizationRequest) -> OptimizedRoute:
        """Optimize route using nearest neighbor algorithm"""
        
        # Geocode vehicle start location if needed
        vehicle = request.vehicle
        if not vehicle.start_latitude or not vehicle.start_longitude:
            lat, lon = self.geocoding_service.geocode_address(vehicle.start_location)
            if lat and lon:
                vehicle.start_latitude = lat
                vehicle.start_longitude = lon
            else:
                raise ValueError(f"Could not geocode vehicle start location: {vehicle.start_location}")
        
        # Geocode delivery locations if needed
        locations = []
        for loc in request.locations:
            if not loc.latitude or not loc.longitude:
                lat, lon = self.geocoding_service.geocode_address(loc.address)
                if lat and lon:
                    loc.latitude = lat
                    loc.longitude = lon
                else:
                    print(f"Warning: Could not geocode {loc.address}, skipping")
                    continue
            locations.append(loc)
        
        if not locations:
            raise ValueError("No valid locations found after geocoding")
        
        # Sort by priority first (1=highest priority)
        locations.sort(key=lambda x: x.priority)
        
        # Simple nearest neighbor optimization starting from vehicle location
        current_pos = (vehicle.start_latitude, vehicle.start_longitude)
        unvisited = locations.copy()
        route_stops = []
        total_distance = 0.0
        total_time = 0
        sequence = 1
        
        while unvisited:
            # Find nearest unvisited location
            nearest_loc = None
            min_distance = float('inf')
            
            for loc in unvisited:
                distance = geodesic(current_pos, (loc.latitude, loc.longitude)).kilometers
                if distance < min_distance:
                    min_distance = distance
                    nearest_loc = loc
            
            # Add to route
            travel_time = int(min_distance * 2)  # Rough estimate: 2 minutes per km
            route_stops.append(RouteStop(
                order_id=nearest_loc.order_id,
                address=nearest_loc.address,
                latitude=nearest_loc.latitude,
                longitude=nearest_loc.longitude,
                sequence=sequence,
                distance_from_previous=round(min_distance, 2),
                estimated_travel_time=travel_time,
                priority=nearest_loc.priority
            ))
            
            total_distance += min_distance
            total_time += travel_time + 10  # Add 10 minutes service time
            sequence += 1
            current_pos = (nearest_loc.latitude, nearest_loc.longitude)
            unvisited.remove(nearest_loc)
        
        return OptimizedRoute(
            vehicle_id=vehicle.vehicle_id,
            total_distance=round(total_distance, 2),
            total_time=total_time,
            total_stops=len(route_stops),
            route_stops=route_stops
        )

# Initialize optimizer
optimizer = SimpleRouteOptimizer()

@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_route(request: OptimizationRequest):
    """
    Optimize route for a single vehicle with multiple delivery locations
    
    Takes order IDs and locations, returns optimized delivery route.
    """
    try:
        # Validate input
        if not request.locations:
            raise HTTPException(status_code=400, detail="No delivery locations provided")
        
        if len(request.locations) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 locations allowed per request")
        
        # Optimize route
        optimized_route = optimizer.optimize_route(request)
        
        return OptimizationResponse(
            status="success",
            message=f"Route optimized successfully for {optimized_route.total_stops} stops",
            optimized_route=optimized_route
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

@router.post("/quick-optimize")
async def quick_optimize(
    vehicle_start_address: str,
    order_locations: List[Dict[str, Any]]
):
    """
    Quick optimization endpoint with minimal input requirements
    
    Expected format:
    {
        "vehicle_start_address": "123 Main St, City, State",
        "order_locations": [
            {"order_id": "ORD001", "address": "456 Oak St, City, State"},
            {"order_id": "ORD002", "address": "789 Pine Ave, City, State"}
        ]
    }
    """
    try:
        # Convert to internal format
        vehicle = VehicleRequest(
            vehicle_id="VEHICLE_001",
            start_location=vehicle_start_address
        )
        
        locations = []
        for i, loc in enumerate(order_locations):
            if "order_id" not in loc or "address" not in loc:
                raise HTTPException(status_code=400, detail=f"Location {i+1} missing order_id or address")
            
            locations.append(LocationRequest(
                order_id=loc["order_id"],
                address=loc["address"],
                priority=loc.get("priority", 2)
            ))
        
        request = OptimizationRequest(
            vehicle=vehicle,
            locations=locations
        )
        
        # Optimize
        optimized_route = optimizer.optimize_route(request)
        
        return {
            "status": "success",
            "vehicle_id": optimized_route.vehicle_id,
            "total_distance_km": optimized_route.total_distance,
            "total_time_minutes": optimized_route.total_time,
            "route": [
                {
                    "sequence": stop.sequence,
                    "order_id": stop.order_id,
                    "address": stop.address,
                    "distance_from_previous_km": stop.distance_from_previous,
                    "travel_time_minutes": stop.estimated_travel_time
                }
                for stop in optimized_route.route_stops
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick optimization failed: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Route Optimization API",
        "endpoints": [
            "POST /optimize - Full optimization with detailed parameters",
            "POST /quick-optimize - Simple optimization with minimal input"
        ]
    }
