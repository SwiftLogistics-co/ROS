from fastapi import APIRouter
from app.api.v1.endpoints import vehicles, addresses, routes, ros_routes, simple_optimization, supabase_routes

api_router = APIRouter()

# Main Supabase-integrated optimization endpoints
api_router.include_router(supabase_routes.router, prefix="/api", tags=["route-optimization"])

# Simplified optimization endpoint
api_router.include_router(simple_optimization.router, prefix="/optimization", tags=["optimization"])

# Legacy endpoints for complex use cases
api_router.include_router(vehicles.router, prefix="/vehicles", tags=["vehicles"])
api_router.include_router(addresses.router, prefix="/addresses", tags=["addresses"]) 
api_router.include_router(routes.router, prefix="/routes", tags=["routes"])
api_router.include_router(ros_routes.router, prefix="/ros", tags=["ros-pipeline"])
