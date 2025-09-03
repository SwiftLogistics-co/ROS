import asyncio
import httpx
from typing import List, Dict, Tuple, Optional
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import json
import time
from app.db.models import Address, Vehicle
from app.core.config import settings


class GeocodingService:
    """Step 1: Geocoding service using Nominatim"""
    
    def __init__(self):
        self.geocoder = Nominatim(
            user_agent="ROS_SwiftLogistics",
            timeout=10
        )
        self.cache = {}  # Simple in-memory cache
    
    def geocode_address(self, address: Address) -> Tuple[float, float]:
        """Geocode a single address to get lat/lon coordinates"""
        # Return cached coordinates if available
        if address.latitude and address.longitude:
            return address.latitude, address.longitude
        
        # Create cache key
        cache_key = f"{address.street_address}_{address.city}_{address.state}_{address.postal_code}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Format full address for geocoding
        full_address = self._format_address(address)
        
        try:
            location = self.geocoder.geocode(full_address)
            if location:
                coords = (location.latitude, location.longitude)
                self.cache[cache_key] = coords
                return coords
            else:
                print(f"Geocoding failed: No results for {full_address}")
                return (0.0, 0.0)
                
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"Geocoding error for {full_address}: {e}")
            return (0.0, 0.0)
    
    def batch_geocode_addresses(self, addresses: List[Address]) -> Dict[int, Tuple[float, float]]:
        """Batch geocode multiple addresses"""
        results = {}
        
        for address in addresses:
            coords = self.geocode_address(address)
            results[address.id] = coords
            # Add small delay to respect Nominatim usage policy
            time.sleep(1)
        
        return results
    
    def _format_address(self, address: Address) -> str:
        """Format address for geocoding"""
        components = [
            address.street_address,
            address.city,
            address.state,
            address.postal_code,
            address.country
        ]
        return ", ".join(filter(None, components))


class VROOMService:
    """Step 2: VROOM optimization service integration"""
    
    def __init__(self, vroom_url: str = "http://localhost:3000"):
        self.vroom_url = vroom_url
        self.client = httpx.AsyncClient()
    
    async def create_vroom_job(self, vehicles: List[Vehicle], addresses: List[Address], 
                              coordinates: Dict[int, Tuple[float, float]]) -> Dict:
        """Create VROOM optimization job"""
        
        # Convert vehicles to VROOM format
        vroom_vehicles = []
        for i, vehicle in enumerate(vehicles):
            # Use depot coordinates (simplified - use first valid address for demo)
            depot_coords = list(coordinates.values())[0] if coordinates else [0.0, 0.0]
            
            vroom_vehicle = {
                "id": vehicle.id,
                "start": depot_coords,
                "end": depot_coords,
                "capacity": [int(vehicle.capacity)],
                "skills": [1],  # Basic skill set
                "time_window": [480, 1020]  # 8 AM to 5 PM in minutes
            }
            vroom_vehicles.append(vroom_vehicle)
        
        # Convert addresses to VROOM jobs
        vroom_jobs = []
        for address in addresses:
            coords = coordinates.get(address.id, (0.0, 0.0))
            
            vroom_job = {
                "id": address.id,
                "location": [coords[1], coords[0]],  # VROOM uses [lon, lat]
                "delivery": [int(address.delivery_weight)],
                "service": address.service_time * 60,  # Convert to seconds
                "skills": [1],
                "priority": address.priority
            }
            
            # Add time windows if specified
            if address.time_window_start and address.time_window_end:
                start_minutes = self._time_to_minutes(address.time_window_start)
                end_minutes = self._time_to_minutes(address.time_window_end)
                vroom_job["time_windows"] = [[start_minutes * 60, end_minutes * 60]]  # Convert to seconds
            
            vroom_jobs.append(vroom_job)
        
        # Create VROOM problem definition
        vroom_problem = {
            "vehicles": vroom_vehicles,
            "jobs": vroom_jobs,
            "options": {
                "g": True  # Use geometry (requires OSRM)
            }
        }
        
        return vroom_problem
    
    async def solve_optimization(self, vroom_problem: Dict) -> Dict:
        """Send problem to VROOM and get solution"""
        try:
            response = await self.client.post(
                f"{self.vroom_url}/",
                json=vroom_problem,
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            print(f"VROOM optimization failed: {e}")
            return {"error": str(e)}
    
    def _time_to_minutes(self, time_str: str) -> int:
        """Convert HH:MM format to minutes since midnight"""
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes


class OSRMService:
    """OSRM routing service for distance/time calculations"""
    
    def __init__(self, osrm_url: str = "http://localhost:5000"):
        self.osrm_url = osrm_url
        self.client = httpx.AsyncClient()
    
    async def get_route_matrix(self, coordinates: List[Tuple[float, float]]) -> Dict:
        """Get distance and time matrix between coordinates"""
        # Format coordinates for OSRM (lon,lat format)
        coord_string = ";".join([f"{lon},{lat}" for lat, lon in coordinates])
        
        try:
            response = await self.client.get(
                f"{self.osrm_url}/table/v1/driving/{coord_string}",
                params={
                    "annotations": "distance,duration"
                }
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            print(f"OSRM matrix request failed: {e}")
            return {"error": str(e)}
    
    async def get_route_geometry(self, coordinates: List[Tuple[float, float]]) -> Dict:
        """Get route geometry between coordinates"""
        coord_string = ";".join([f"{lon},{lat}" for lat, lon in coordinates])
        
        try:
            response = await self.client.get(
                f"{self.osrm_url}/route/v1/driving/{coord_string}",
                params={
                    "overview": "full",
                    "geometries": "geojson"
                }
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            print(f"OSRM route request failed: {e}")
            return {"error": str(e)}


class ROSPipelineService:
    """Main ROS Pipeline orchestrator"""
    
    def __init__(self):
        self.geocoding_service = GeocodingService()
        self.vroom_service = VROOMService()
        self.osrm_service = OSRMService()
    
    async def process_optimization_request(self, vehicles: List[Vehicle], 
                                         addresses: List[Address]) -> Dict:
        """
        Complete ROS pipeline:
        Step 1: Geocoding with Nominatim
        Step 2: Route optimization with VROOM + OSRM
        Step 3: Return optimized routes
        """
        
        # Step 1: Geocoding
        print("Step 1: Geocoding addresses...")
        coordinates = self.geocoding_service.batch_geocode_addresses(addresses)
        
        # Filter out failed geocoding results
        valid_addresses = [addr for addr in addresses if coordinates[addr.id] != (0.0, 0.0)]
        valid_coordinates = {addr_id: coords for addr_id, coords in coordinates.items() 
                           if coords != (0.0, 0.0)}
        
        if not valid_addresses:
            return {"error": "No addresses could be geocoded"}
        
        print(f"Successfully geocoded {len(valid_addresses)} out of {len(addresses)} addresses")
        
        # Step 2: Route optimization
        print("Step 2: Creating VROOM optimization job...")
        vroom_problem = await self.vroom_service.create_vroom_job(
            vehicles, valid_addresses, valid_coordinates
        )
        
        print("Step 2: Solving optimization with VROOM...")
        vroom_solution = await self.vroom_service.solve_optimization(vroom_problem)
        
        if "error" in vroom_solution:
            # Fallback to basic optimization if VROOM fails
            print("VROOM failed, using fallback optimization...")
            return await self._fallback_optimization(vehicles, valid_addresses, valid_coordinates)
        
        # Step 3: Process and return results
        print("Step 3: Processing optimization results...")
        return self._process_vroom_solution(vroom_solution, vehicles, valid_addresses, valid_coordinates)
    
    async def _fallback_optimization(self, vehicles: List[Vehicle], 
                                   addresses: List[Address], 
                                   coordinates: Dict[int, Tuple[float, float]]) -> Dict:
        """Fallback optimization using built-in algorithms"""
        from app.services.optimization import RouteOptimizationService
        from app.schemas.schemas import OptimizationRequest
        
        optimization_service = RouteOptimizationService()
        request = OptimizationRequest(
            vehicle_ids=[v.id for v in vehicles],
            address_ids=[a.id for a in addresses],
            optimization_type="distance"
        )
        
        return optimization_service.optimize_routes(request, vehicles, addresses)
    
    def _process_vroom_solution(self, solution: Dict, vehicles: List[Vehicle], 
                               addresses: List[Address], 
                               coordinates: Dict[int, Tuple[float, float]]) -> Dict:
        """Process VROOM solution into ROS format"""
        
        routes = []
        total_distance = 0
        total_time = 0
        total_cost = 0
        
        for route_data in solution.get("routes", []):
            vehicle_id = route_data["vehicle"]
            vehicle = next((v for v in vehicles if v.id == vehicle_id), None)
            
            if not vehicle:
                continue
            
            stops = []
            route_distance = route_data.get("distance", 0) / 1000  # Convert to km
            route_time = route_data.get("duration", 0) / 60       # Convert to minutes
            route_cost = route_distance * vehicle.cost_per_km
            
            for i, step in enumerate(route_data.get("steps", [])):
                if step["type"] == "job":
                    job_id = step["job"]
                    address = next((a for a in addresses if a.id == job_id), None)
                    
                    if address:
                        stops.append({
                            "address_id": address.id,
                            "sequence": i,
                            "estimated_arrival": self._seconds_to_time(step.get("arrival", 0)),
                            "distance_from_previous": step.get("distance", 0) / 1000,
                            "time_from_previous": step.get("duration", 0) / 60
                        })
            
            routes.append({
                "vehicle_id": vehicle_id,
                "stops": stops,
                "total_distance": round(route_distance, 2),
                "total_time": int(route_time),
                "total_cost": round(route_cost, 2)
            })
            
            total_distance += route_distance
            total_time = max(total_time, route_time)
            total_cost += route_cost
        
        return {
            "routes": routes,
            "total_distance": round(total_distance, 2),
            "total_time": int(total_time),
            "total_cost": round(total_cost, 2),
            "optimization_time": solution.get("computing_times", {}).get("total", 0) / 1000,
            "geocoded_addresses": len(coordinates),
            "optimization_engine": "VROOM"
        }
    
    def _seconds_to_time(self, seconds: int) -> str:
        """Convert seconds since midnight to HH:MM format"""
        minutes = seconds // 60
        hours = minutes // 60
        minutes = minutes % 60
        return f"{hours:02d}:{minutes:02d}"
