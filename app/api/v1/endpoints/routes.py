from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models
from app.schemas.schemas import (
    Route, RouteCreate, OptimizationRequest, OptimizationResult, ResponseMessage,
    CoordinateOptimizationRequest, OptimizedRouteResponse
)
from app.services.optimization import RouteOptimizationService
import math

router = APIRouter()
optimization_service = RouteOptimizationService()


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


@router.post("/optimize-coordinates")
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


@router.post("/optimize", response_model=OptimizationResult)
async def optimize_routes(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Optimize routes for given vehicles and addresses"""
    
    # Fetch vehicles and addresses from database
    vehicles = db.query(models.Vehicle).filter(
        models.Vehicle.id.in_(request.vehicle_ids),
        models.Vehicle.is_available == True
    ).all()
    
    addresses = db.query(models.Address).filter(
        models.Address.id.in_(request.address_ids)
    ).all()
    
    if not vehicles:
        raise HTTPException(status_code=404, detail="No available vehicles found")
    
    if not addresses:
        raise HTTPException(status_code=404, detail="No addresses found")
    
    try:
        # Perform optimization
        result = optimization_service.optimize_routes(request, vehicles, addresses)
        
        # Save routes to database in background
        background_tasks.add_task(save_optimized_routes, result['routes'], db)
        
        # Convert route data to proper response format
        route_objects = []
        for route_data in result['routes']:
            vehicle = next(v for v in vehicles if v.id == route_data['vehicle_id'])
            route_obj = {
                'id': 0,  # Will be set when saved to DB
                'name': f"Route for {vehicle.name}",
                'vehicle_id': route_data['vehicle_id'],
                'total_distance': route_data['total_distance'],
                'total_time': route_data['total_time'],
                'total_cost': route_data['total_cost'],
                'optimization_status': 'completed',
                'vehicle': vehicle,
                'stops': []
            }
            route_objects.append(route_obj)
        
        return OptimizationResult(
            routes=route_objects,
            total_distance=result['total_distance'],
            total_time=result['total_time'],
            total_cost=result['total_cost'],
            optimization_time=result['optimization_time']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.get("/", response_model=List[Route])
def list_routes(
    skip: int = 0,
    limit: int = 100,
    vehicle_id: int = None,
    db: Session = Depends(get_db)
):
    """List all routes with optional filtering"""
    query = db.query(models.Route)
    
    if vehicle_id:
        query = query.filter(models.Route.vehicle_id == vehicle_id)
    
    routes = query.offset(skip).limit(limit).all()
    return routes


@router.get("/{route_id}", response_model=Route)
def get_route(route_id: int, db: Session = Depends(get_db)):
    """Get route by ID with all stops"""
    route = db.query(models.Route).filter(models.Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route


@router.delete("/{route_id}", response_model=ResponseMessage)
def delete_route(route_id: int, db: Session = Depends(get_db)):
    """Delete route and all its stops"""
    route = db.query(models.Route).filter(models.Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Delete route stops first
    db.query(models.RouteStop).filter(models.RouteStop.route_id == route_id).delete()
    
    # Delete route
    db.delete(route)
    db.commit()
    
    return ResponseMessage(message=f"Route {route_id} deleted successfully")


def save_optimized_routes(routes_data: List[dict], db: Session):
    """Background task to save optimized routes to database"""
    try:
        for route_data in routes_data:
            # Create route
            db_route = models.Route(
                name=f"Optimized Route {route_data['vehicle_id']}",
                vehicle_id=route_data['vehicle_id'],
                total_distance=route_data['total_distance'],
                total_time=route_data['total_time'],
                total_cost=route_data['total_cost'],
                optimization_status='completed'
            )
            db.add(db_route)
            db.flush()  # Get the route ID
            
            # Create route stops
            for stop_data in route_data['stops']:
                db_stop = models.RouteStop(
                    route_id=db_route.id,
                    address_id=stop_data['address_id'],
                    sequence=stop_data['sequence'],
                    estimated_arrival=stop_data['estimated_arrival'],
                    distance_from_previous=stop_data['distance_from_previous'],
                    time_from_previous=stop_data['time_from_previous']
                )
                db.add(db_stop)
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Failed to save routes: {e}")
