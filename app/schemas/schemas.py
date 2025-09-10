from typing import List, Optional
from pydantic import BaseModel, validator
from datetime import datetime


# Vehicle Schemas
class VehicleBase(BaseModel):
    name: str
    vehicle_type: str
    capacity: float
    max_distance: float
    cost_per_km: float
    start_location: str
    is_available: bool = True


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    name: Optional[str] = None
    vehicle_type: Optional[str] = None
    capacity: Optional[float] = None
    max_distance: Optional[float] = None
    cost_per_km: Optional[float] = None
    start_location: Optional[str] = None
    is_available: Optional[bool] = None


class Vehicle(VehicleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Address Schemas
class AddressBase(BaseModel):
    name: str
    street_address: str
    city: str
    state: str
    postal_code: str
    country: str
    delivery_weight: float
    delivery_volume: float
    time_window_start: Optional[str] = None
    time_window_end: Optional[str] = None
    service_time: int = 15
    priority: int = 1
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @validator('priority')
    def validate_priority(cls, v):
        if v not in [1, 2, 3]:
            raise ValueError('Priority must be 1 (low), 2 (medium), or 3 (high)')
        return v


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    name: Optional[str] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    delivery_weight: Optional[float] = None
    delivery_volume: Optional[float] = None
    time_window_start: Optional[str] = None
    time_window_end: Optional[str] = None
    service_time: Optional[int] = None
    priority: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class Address(AddressBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Route Stop Schemas
class RouteStopBase(BaseModel):
    address_id: int
    sequence: int
    estimated_arrival: Optional[str] = None
    distance_from_previous: float
    time_from_previous: int


class RouteStop(RouteStopBase):
    id: int
    route_id: int
    address: Address

    class Config:
        from_attributes = True


# Route Schemas
class RouteBase(BaseModel):
    name: str
    vehicle_id: int
    total_distance: float
    total_time: int
    total_cost: float
    optimization_status: str = "pending"


class RouteCreate(BaseModel):
    name: str
    vehicle_id: int
    address_ids: List[int]


class Route(RouteBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    vehicle: Vehicle
    stops: List[RouteStop] = []

    class Config:
        from_attributes = True


# Route Optimization Schemas
class OptimizationRequest(BaseModel):
    vehicle_ids: List[int]
    address_ids: List[int]
    optimization_type: str = "distance"  # distance, time, cost

    @validator('optimization_type')
    def validate_optimization_type(cls, v):
        if v not in ['distance', 'time', 'cost']:
            raise ValueError('Optimization type must be distance, time, or cost')
        return v


class OptimizationResult(BaseModel):
    routes: List[Route]
    total_distance: float
    total_time: int
    total_cost: float
    optimization_time: float  # seconds taken to optimize


# Coordinate-based Route Optimization Schemas
class Coordinate(BaseModel):
    lat: float
    lng: float


class OrderItem(BaseModel):
    order_id: int
    address: str
    coordinate: Coordinate


class OrdersContainer(BaseModel):
    order: List[OrderItem]


class CoordinateOptimizationRequest(BaseModel):
    response: dict  # Contains the nested structure


class OptimizedRouteResponse(BaseModel):
    status: str
    message: str
    optimization_summary: dict
    optimized_route: dict


# Response Schemas
class ResponseMessage(BaseModel):
    message: str
    status: str = "success"


class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    size: int
    pages: int
