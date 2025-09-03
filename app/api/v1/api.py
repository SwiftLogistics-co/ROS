from fastapi import APIRouter
from app.api.v1.endpoints import vehicles, addresses, routes, ros_routes

api_router = APIRouter()

api_router.include_router(vehicles.router, prefix="/vehicles", tags=["vehicles"])
api_router.include_router(addresses.router, prefix="/addresses", tags=["addresses"])
api_router.include_router(routes.router, prefix="/routes", tags=["routes"])
api_router.include_router(ros_routes.router, prefix="/ros", tags=["ros-pipeline"])
