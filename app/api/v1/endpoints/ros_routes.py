from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models
from app.schemas.schemas import (
    OptimizationRequest, OptimizationResult, ResponseMessage
)
from app.services.ros_pipeline import ROSPipelineService

router = APIRouter()
ros_pipeline = ROSPipelineService()


@router.post("/optimize-advanced", response_model=dict)
async def optimize_routes_advanced(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Advanced route optimization using the complete ROS pipeline:
    Step 1: Geocoding with Nominatim
    Step 2: Route optimization with VROOM + OSRM
    Step 3: Return optimized routes
    """
    
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
        # Process through ROS pipeline
        result = await ros_pipeline.process_optimization_request(vehicles, addresses)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Save routes to database in background
        background_tasks.add_task(save_optimized_routes, result['routes'], db)
        
        return {
            "status": "success",
            "optimization_engine": result.get("optimization_engine", "ROS"),
            "geocoded_addresses": result.get("geocoded_addresses", len(addresses)),
            "total_addresses": len(addresses),
            "routes": result['routes'],
            "summary": {
                "total_distance_km": result['total_distance'],
                "total_time_minutes": result['total_time'],
                "total_cost": result['total_cost'],
                "optimization_time_seconds": result['optimization_time'],
                "number_of_routes": len(result['routes'])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ROS Pipeline failed: {str(e)}")


@router.post("/geocode-batch")
async def batch_geocode_addresses(
    address_ids: List[int],
    db: Session = Depends(get_db)
):
    """Batch geocode addresses and update their coordinates in the database"""
    
    addresses = db.query(models.Address).filter(
        models.Address.id.in_(address_ids)
    ).all()
    
    if not addresses:
        raise HTTPException(status_code=404, detail="No addresses found")
    
    try:
        # Geocode addresses
        coordinates = ros_pipeline.geocoding_service.batch_geocode_addresses(addresses)
        
        # Update database with coordinates
        updated_count = 0
        for address in addresses:
            coords = coordinates.get(address.id)
            if coords and coords != (0.0, 0.0):
                address.latitude = coords[0]
                address.longitude = coords[1]
                updated_count += 1
        
        db.commit()
        
        return {
            "status": "success",
            "total_addresses": len(addresses),
            "geocoded_successfully": updated_count,
            "geocoded_coordinates": {
                addr_id: {"lat": coords[0], "lon": coords[1]} 
                for addr_id, coords in coordinates.items() 
                if coords != (0.0, 0.0)
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Geocoding failed: {str(e)}")


def save_optimized_routes(routes_data: List[dict], db: Session):
    """Background task to save optimized routes to database"""
    try:
        for route_data in routes_data:
            # Create route
            db_route = models.Route(
                name=f"ROS Optimized Route {route_data['vehicle_id']}",
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
