from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

router = APIRouter()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Warning: Supabase credentials not found in environment variables")
    supabase: Client = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Request/Response Models
class OrderLocation(BaseModel):
    order_id: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    priority: Optional[int] = 1  # 1=high, 2=medium, 3=low

class RouteOptimizationRequest(BaseModel):
    start_location: str
    end_location: str
    order_locations: List[OrderLocation]
    driver_id: Optional[int] = None
    route_name: Optional[str] = None

class RouteStop(BaseModel):
    sequence: int
    order_id: str
    address: str
    latitude: float
    longitude: float
    distance_from_previous_km: float
    estimated_travel_time_minutes: int

class OptimizedRouteResponse(BaseModel):
    status: str
    id: int
    route_name: str
    driver_id: Optional[int]
    start_location: str
    end_location: str
    total_distance_km: float
    total_time_minutes: int
    total_orders: int
    optimized_route: List[RouteStop]
    created_at: str

# Simple Route Optimizer
class SupabaseRouteOptimizer:
    def __init__(self):
        self.geocoder = Nominatim(user_agent="ROS_Supabase_API", timeout=10)
    
    def geocode_address(self, address: str) -> tuple:
        """Geocode address to lat/lon coordinates"""
        try:
            location = self.geocoder.geocode(address)
            if location:
                return location.latitude, location.longitude
            return None, None
        except Exception as e:
            print(f"Geocoding error for {address}: {e}")
            return None, None
    
    def optimize_route(self, request: RouteOptimizationRequest) -> OptimizedRouteResponse:
        """Optimize delivery route using nearest neighbor algorithm"""
        
        # Geocode start location
        start_lat, start_lon = self.geocode_address(request.start_location)
        if not start_lat or not start_lon:
            raise ValueError(f"Could not geocode start location: {request.start_location}")
        
        # Geocode end location
        end_lat, end_lon = self.geocode_address(request.end_location)
        if not end_lat or not end_lon:
            raise ValueError(f"Could not geocode end location: {request.end_location}")
        
        # Geocode all order locations
        valid_locations = []
        for order in request.order_locations:
            if order.latitude and order.longitude:
                # Use provided coordinates
                valid_locations.append(order)
            else:
                # Geocode the address
                lat, lon = self.geocode_address(order.address)
                if lat and lon:
                    order.latitude = lat
                    order.longitude = lon
                    valid_locations.append(order)
                else:
                    print(f"Warning: Could not geocode order {order.order_id} at {order.address}")
        
        if not valid_locations:
            raise ValueError("No valid order locations found after geocoding")
        
        # Sort by priority (1 = highest priority first)
        valid_locations.sort(key=lambda x: x.priority or 1)
        
        # Optimize route using nearest neighbor algorithm
        current_pos = (start_lat, start_lon)
        unvisited = valid_locations.copy()
        optimized_stops = []
        total_distance = 0.0
        total_time = 0
        sequence = 1
        
        while unvisited:
            # Find nearest unvisited location
            nearest_order = None
            min_distance = float('inf')
            
            for order in unvisited:
                distance = geodesic(current_pos, (order.latitude, order.longitude)).kilometers
                if distance < min_distance:
                    min_distance = distance
                    nearest_order = order
            
            # Add to optimized route
            travel_time = max(int(min_distance * 2.5), 5)  # Estimate: 2.5 min per km, minimum 5 min
            
            optimized_stops.append(RouteStop(
                sequence=sequence,
                order_id=nearest_order.order_id,
                address=nearest_order.address,
                latitude=nearest_order.latitude,
                longitude=nearest_order.longitude,
                distance_from_previous_km=round(min_distance, 2),
                estimated_travel_time_minutes=travel_time
            ))
            
            total_distance += min_distance
            total_time += travel_time + 10  # Add 10 minutes service time per stop
            sequence += 1
            current_pos = (nearest_order.latitude, nearest_order.longitude)
            unvisited.remove(nearest_order)
        
        # Add final distance to end location
        final_distance = geodesic(current_pos, (end_lat, end_lon)).kilometers
        total_distance += final_distance
        total_time += max(int(final_distance * 2.5), 5)
        
        # Generate route name if not provided
        route_name = request.route_name or f"Route_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return OptimizedRouteResponse(
            status="success",
            id=0,  # Will be set when saved to database
            route_name=route_name,
            driver_id=request.driver_id,
            start_location=request.start_location,
            end_location=request.end_location,
            total_distance_km=round(total_distance, 2),
            total_time_minutes=total_time,
            total_orders=len(optimized_stops),
            optimized_route=optimized_stops,
            created_at=datetime.now().isoformat()
        )

# Initialize optimizer
optimizer = SupabaseRouteOptimizer()

@router.post("/optimize-route", response_model=OptimizedRouteResponse)
async def optimize_delivery_route(request: RouteOptimizationRequest):
    """
    Optimize delivery route for orders
    
    Takes:
    - Start location 
    - End location
    - List of order locations (with order IDs)
    - Optional driver ID
    
    Returns optimized route with sequence and timing
    """
    try:
        # Validate input
        if not request.order_locations:
            raise HTTPException(status_code=400, detail="No order locations provided")
        
        if len(request.order_locations) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 orders allowed per route")
        
        # Optimize the route
        optimized_route = optimizer.optimize_route(request)
        
        # Save to Supabase if available
        if supabase:
            try:
                # Save route to your existing routes table
                route_data = {
                    "route_name": optimized_route.route_name,
                    "driver_id": optimized_route.driver_id,
                    "start_location": optimized_route.start_location,
                    "end_location": optimized_route.end_location,
                    "total_distance_km": optimized_route.total_distance_km,
                    "total_time_minutes": optimized_route.total_time_minutes,
                    "total_orders": optimized_route.total_orders,
                    "route_data": [stop.dict() for stop in optimized_route.optimized_route],
                    "optimization_status": "optimized"
                }
                
                result = supabase.table("routes").insert(route_data).execute()
                if result.data:
                    optimized_route.id = result.data[0]["id"]
                    print(f"Route saved to Supabase: {optimized_route.route_name}")
                
            except Exception as e:
                print(f"Failed to save route to Supabase: {e}")
                # Continue without saving - don't fail the optimization
        
        return optimized_route
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route optimization failed: {str(e)}")

@router.post("/simple-optimize")
async def simple_route_optimize(
    start_location: str,
    end_location: str,
    orders: List[Dict[str, Any]],
    driver_id: Optional[int] = None,
    route_name: Optional[str] = None
):
    """
    Ultra-simple route optimization endpoint
    
    POST /simple-optimize
    {
        "start_location": "Colombo Fort",
        "end_location": "Nugegoda", 
        "orders": [
            {"order_id": "ORD001", "address": "456 Galle Road, Colombo"},
            {"order_id": "ORD002", "address": "789 Kandy Road, Colombo"}
        ],
        "driver_id": 1,
        "route_name": "Colombo City Express"
    }
    """
    try:
        # Convert to internal format
        order_locations = []
        for order in orders:
            if "order_id" not in order or "address" not in order:
                raise HTTPException(status_code=400, detail="Each order must have 'order_id' and 'address'")
            
            order_locations.append(OrderLocation(
                order_id=order["order_id"],
                address=order["address"],
                priority=order.get("priority", 1)
            ))
        
        request = RouteOptimizationRequest(
            start_location=start_location,
            end_location=end_location,
            order_locations=order_locations,
            driver_id=driver_id,
            route_name=route_name or f"Route_{datetime.now().strftime('%H%M%S')}"
        )
        
        # Optimize route
        result = optimizer.optimize_route(request)
        
        # Save to Supabase if available
        saved_id = None
        if supabase:
            try:
                route_data = {
                    "route_name": result.route_name,
                    "driver_id": result.driver_id,
                    "start_location": result.start_location,
                    "end_location": result.end_location,
                    "total_distance_km": result.total_distance_km,
                    "total_time_minutes": result.total_time_minutes,
                    "total_orders": result.total_orders,
                    "route_data": [stop.dict() for stop in result.optimized_route],
                    "optimization_status": "optimized"
                }
                
                save_result = supabase.table("routes").insert(route_data).execute()
                if save_result.data:
                    saved_id = save_result.data[0]["id"]
                    
            except Exception as e:
                print(f"Failed to save route to Supabase: {e}")
        
        # Return simplified response
        return {
            "status": "success",
            "id": saved_id,
            "route_name": result.route_name,
            "driver_id": result.driver_id,
            "start_location": result.start_location,
            "end_location": result.end_location,
            "total_distance_km": result.total_distance_km,
            "total_time_minutes": result.total_time_minutes,
            "total_orders": result.total_orders,
            "route": [
                {
                    "stop": stop.sequence,
                    "order_id": stop.order_id,
                    "address": stop.address,
                    "distance_km": stop.distance_from_previous_km,
                    "travel_time_min": stop.estimated_travel_time_minutes
                }
                for stop in result.optimized_route
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route optimization failed: {str(e)}")

@router.post("/optimize-driver-route")
async def optimize_driver_route(
    driver_id: int,
    start_location: str,
    end_location: str,
    order_locations: List[Dict[str, Any]],
    route_name: Optional[str] = None
):
    """
    Optimize route for a specific driver with order IDs and locations
    
    POST /optimize-driver-route
    {
        "driver_id": 1,
        "start_location": "Colombo Fort",
        "end_location": "Nugegoda",
        "order_locations": [
            {"order_id": "ORD001", "location": "Galle Road, Colombo", "priority": 1},
            {"order_id": "ORD002", "location": "Kandy Road, Colombo", "priority": 2}
        ],
        "route_name": "Colombo City Express"
    }
    """
    try:
        # Validate input
        if not order_locations:
            raise HTTPException(status_code=400, detail="No order locations provided")
        
        if len(order_locations) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 orders allowed per route")
        
        # Convert order locations to internal format
        orders = []
        for order in order_locations:
            if "order_id" not in order or "location" not in order:
                raise HTTPException(status_code=400, detail="Each order must have 'order_id' and 'location'")
            
            orders.append(OrderLocation(
                order_id=order["order_id"],
                address=order["location"],
                priority=order.get("priority", 1)
            ))
        
        # Create optimization request
        request = RouteOptimizationRequest(
            start_location=start_location,
            end_location=end_location,
            order_locations=orders,
            driver_id=driver_id,
            route_name=route_name or f"Driver_{driver_id}_Route_{datetime.now().strftime('%H%M%S')}"
        )
        
        # Optimize the route
        optimized_route = optimizer.optimize_route(request)
        
        # Save to Supabase routes table
        saved_id = None
        if supabase:
            try:
                route_data = {
                    "route_name": optimized_route.route_name,
                    "driver_id": driver_id,
                    "start_location": start_location,
                    "end_location": end_location
                }
                
                # Add optimization data if columns exist
                try:
                    route_data.update({
                        "total_distance_km": optimized_route.total_distance_km,
                        "total_time_minutes": optimized_route.total_time_minutes,
                        "total_orders": optimized_route.total_orders,
                        "route_data": [stop.dict() for stop in optimized_route.optimized_route],
                        "optimization_status": "optimized"
                    })
                except:
                    pass  # Continue if these columns don't exist yet
                
                result = supabase.table("routes").insert(route_data).execute()
                if result.data:
                    saved_id = result.data[0]["id"]
                    print(f"Route saved to Supabase with ID: {saved_id}")
                
            except Exception as e:
                print(f"Failed to save route to Supabase: {e}")
        
        # Return optimized route with order details
        return {
            "status": "success",
            "route_id": saved_id,
            "driver_id": driver_id,
            "route_name": optimized_route.route_name,
            "start_location": start_location,
            "end_location": end_location,
            "total_distance_km": optimized_route.total_distance_km,
            "total_time_minutes": optimized_route.total_time_minutes,
            "total_orders": optimized_route.total_orders,
            "optimized_route": [
                {
                    "sequence": stop.sequence,
                    "order_id": stop.order_id,
                    "location": stop.address,
                    "latitude": stop.latitude,
                    "longitude": stop.longitude,
                    "distance_from_previous_km": stop.distance_from_previous_km,
                    "estimated_travel_time_minutes": stop.estimated_travel_time_minutes
                }
                for stop in optimized_route.optimized_route
            ]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route optimization failed: {str(e)}")

@router.get("/route/{route_id}")
async def get_route(route_id: int):
    """Get a route by ID from your routes table"""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase not configured")
    
    try:
        result = supabase.table("routes").select("*").eq("id", route_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Route not found")
        
        return result.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve route: {str(e)}")

@router.get("/routes")
async def list_routes(limit: int = 10, driver_id: Optional[int] = None):
    """List routes from your routes table"""
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase not configured")
    
    try:
        query = supabase.table("routes").select("id, route_name, driver_id, start_location, end_location, created_at")
        
        if driver_id:
            query = query.eq("driver_id", driver_id)
        
        result = query.order("created_at", desc=True).limit(limit).execute()
        
        return {
            "status": "success",
            "routes": result.data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list routes: {str(e)}")

@router.get("/driver/{driver_id}/routes")
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

@router.get("/health")
async def health_check():
    """API health check"""
    supabase_status = "connected" if supabase else "not configured"
    
    return {
        "status": "healthy",
        "service": "Route Optimization API with Supabase",
        "supabase": supabase_status,
        "endpoints": {
            "POST /optimize-driver-route": "Optimize route for driver with order IDs",
            "POST /optimize-route": "Full route optimization",
            "POST /simple-optimize": "Simple route optimization", 
            "GET /route/{route_id}": "Get route by ID",
            "GET /routes": "List recent routes",
            "GET /driver/{driver_id}/routes": "Get all routes for a driver"
        }
    }
