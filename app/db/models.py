from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    vehicle_type = Column(String(50), nullable=False)  # van, truck, car, etc.
    capacity = Column(Float, nullable=False)  # in kg or cubic meters
    max_distance = Column(Float, nullable=False)  # maximum distance per day in km
    cost_per_km = Column(Float, nullable=False)
    is_available = Column(Boolean, default=True)
    start_location = Column(String(255), nullable=False)  # depot location
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    routes = relationship("Route", back_populates="vehicle")


class Address(Base):
    __tablename__ = "addresses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    street_address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(50), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(50), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    delivery_weight = Column(Float, nullable=False)  # in kg
    delivery_volume = Column(Float, nullable=False)  # in cubic meters
    time_window_start = Column(String(10), nullable=True)  # HH:MM format
    time_window_end = Column(String(10), nullable=True)    # HH:MM format
    service_time = Column(Integer, default=15)  # minutes required for delivery
    priority = Column(Integer, default=1)  # 1=low, 2=medium, 3=high
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    route_stops = relationship("RouteStop", back_populates="address")


class Route(Base):
    __tablename__ = "routes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    total_distance = Column(Float, nullable=False)  # in km
    total_time = Column(Integer, nullable=False)    # in minutes
    total_cost = Column(Float, nullable=False)      # calculated cost
    optimization_status = Column(String(20), default="pending")  # pending, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="routes")
    stops = relationship("RouteStop", back_populates="route", order_by="RouteStop.sequence")


class RouteStop(Base):
    __tablename__ = "route_stops"
    
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    address_id = Column(Integer, ForeignKey("addresses.id"), nullable=False)
    sequence = Column(Integer, nullable=False)  # order in the route
    estimated_arrival = Column(String(10), nullable=True)  # HH:MM format
    distance_from_previous = Column(Float, nullable=False)  # km from previous stop
    time_from_previous = Column(Integer, nullable=False)    # minutes from previous stop
    
    # Relationships
    route = relationship("Route", back_populates="stops")
    address = relationship("Address", back_populates="route_stops")
