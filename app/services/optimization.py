from typing import List, Tuple, Dict
import math
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import numpy as np
from app.db.models import Vehicle, Address, Route, RouteStop
from app.schemas.schemas import OptimizationRequest
import time


class RouteOptimizationService:
    def __init__(self):
        self.geocoder = Nominatim(user_agent="route_optimization_system")
    
    def geocode_address(self, address: Address) -> Tuple[float, float]:
        """Geocode an address to get latitude and longitude"""
        if address.latitude and address.longitude:
            return address.latitude, address.longitude
        
        full_address = f"{address.street_address}, {address.city}, {address.state}, {address.postal_code}, {address.country}"
        try:
            location = self.geocoder.geocode(full_address)
            if location:
                return location.latitude, location.longitude
        except Exception as e:
            print(f"Geocoding failed for address {address.id}: {e}")
        
        # Return default coordinates if geocoding fails
        return 0.0, 0.0
    
    def calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates in kilometers"""
        return geodesic(coord1, coord2).kilometers
    
    def calculate_travel_time(self, distance_km: float, avg_speed_kmh: float = 50) -> int:
        """Calculate travel time in minutes"""
        return int((distance_km / avg_speed_kmh) * 60)
    
    def create_distance_matrix(self, addresses: List[Address], depot_location: Tuple[float, float]) -> np.ndarray:
        """Create distance matrix between all addresses and depot"""
        coords = [depot_location]  # Start with depot
        
        for address in addresses:
            lat, lon = self.geocode_address(address)
            coords.append((lat, lon))
        
        n = len(coords)
        distance_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    distance_matrix[i][j] = self.calculate_distance(coords[i], coords[j])
        
        return distance_matrix
    
    def nearest_neighbor_tsp(self, distance_matrix: np.ndarray, start_node: int = 0) -> List[int]:
        """Solve TSP using nearest neighbor heuristic"""
        n = distance_matrix.shape[0]
        unvisited = set(range(n))
        current = start_node
        tour = [current]
        unvisited.remove(current)
        
        while unvisited:
            nearest = min(unvisited, key=lambda x: distance_matrix[current][x])
            tour.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        return tour
    
    def two_opt_improvement(self, tour: List[int], distance_matrix: np.ndarray) -> List[int]:
        """Improve tour using 2-opt local search"""
        best_tour = tour[:]
        improved = True
        
        while improved:
            improved = False
            for i in range(1, len(tour) - 2):
                for j in range(i + 1, len(tour)):
                    if j - i == 1:
                        continue
                    
                    new_tour = tour[:]
                    new_tour[i:j] = tour[i:j][::-1]
                    
                    if self.calculate_tour_distance(new_tour, distance_matrix) < \
                       self.calculate_tour_distance(best_tour, distance_matrix):
                        best_tour = new_tour[:]
                        improved = True
            tour = best_tour[:]
        
        return best_tour
    
    def calculate_tour_distance(self, tour: List[int], distance_matrix: np.ndarray) -> float:
        """Calculate total distance of a tour"""
        total_distance = 0
        for i in range(len(tour) - 1):
            total_distance += distance_matrix[tour[i]][tour[i + 1]]
        # Return to start
        total_distance += distance_matrix[tour[-1]][tour[0]]
        return total_distance
    
    def optimize_single_vehicle_route(self, vehicle: Vehicle, addresses: List[Address]) -> Dict:
        """Optimize route for a single vehicle"""
        if not addresses:
            return {
                'vehicle_id': vehicle.id,
                'stops': [],
                'total_distance': 0,
                'total_time': 0,
                'total_cost': 0
            }
        
        # Check vehicle capacity constraints
        total_weight = sum(addr.delivery_weight for addr in addresses)
        total_volume = sum(addr.delivery_volume for addr in addresses)
        
        if total_weight > vehicle.capacity or total_volume > vehicle.capacity:
            raise ValueError(f"Vehicle {vehicle.id} capacity exceeded")
        
        # Get depot coordinates (simplified - using first address city for demo)
        depot_coords = (0.0, 0.0)  # In production, geocode vehicle.start_location
        
        # Create distance matrix
        distance_matrix = self.create_distance_matrix(addresses, depot_coords)
        
        # Solve TSP
        tour = self.nearest_neighbor_tsp(distance_matrix)
        tour = self.two_opt_improvement(tour, distance_matrix)
        
        # Create route stops
        stops = []
        total_distance = 0
        total_time = 0
        current_time = 8 * 60  # Start at 8:00 AM (in minutes)
        
        for i, stop_idx in enumerate(tour[1:], 1):  # Skip depot (index 0)
            address = addresses[stop_idx - 1]  # Adjust for depot offset
            
            distance_from_previous = distance_matrix[tour[i-1]][tour[i]]
            time_from_previous = self.calculate_travel_time(distance_from_previous)
            
            current_time += time_from_previous + address.service_time
            estimated_arrival = f"{current_time // 60:02d}:{current_time % 60:02d}"
            
            stops.append({
                'address_id': address.id,
                'sequence': i,
                'estimated_arrival': estimated_arrival,
                'distance_from_previous': distance_from_previous,
                'time_from_previous': time_from_previous
            })
            
            total_distance += distance_from_previous
            total_time += time_from_previous + address.service_time
        
        # Return to depot
        if stops:
            total_distance += distance_matrix[tour[-1]][tour[0]]
            total_time += self.calculate_travel_time(distance_matrix[tour[-1]][tour[0]])
        
        total_cost = total_distance * vehicle.cost_per_km
        
        return {
            'vehicle_id': vehicle.id,
            'stops': stops,
            'total_distance': round(total_distance, 2),
            'total_time': total_time,
            'total_cost': round(total_cost, 2)
        }
    
    def optimize_multi_vehicle_routes(self, vehicles: List[Vehicle], addresses: List[Address]) -> List[Dict]:
        """Optimize routes for multiple vehicles using simple assignment"""
        if not vehicles or not addresses:
            return []
        
        # Simple strategy: distribute addresses evenly among vehicles
        routes = []
        addresses_per_vehicle = len(addresses) // len(vehicles)
        remainder = len(addresses) % len(vehicles)
        
        start_idx = 0
        for i, vehicle in enumerate(vehicles):
            # Calculate how many addresses this vehicle gets
            end_idx = start_idx + addresses_per_vehicle
            if i < remainder:
                end_idx += 1
            
            vehicle_addresses = addresses[start_idx:end_idx]
            
            if vehicle_addresses:
                route = self.optimize_single_vehicle_route(vehicle, vehicle_addresses)
                routes.append(route)
            
            start_idx = end_idx
        
        return routes
    
    def optimize_routes(self, request: OptimizationRequest, vehicles: List[Vehicle], addresses: List[Address]) -> Dict:
        """Main optimization method"""
        start_time = time.time()
        
        # Filter vehicles and addresses based on request
        selected_vehicles = [v for v in vehicles if v.id in request.vehicle_ids]
        selected_addresses = [a for a in addresses if a.id in request.address_ids]
        
        if not selected_vehicles:
            raise ValueError("No valid vehicles found")
        
        if not selected_addresses:
            raise ValueError("No valid addresses found")
        
        # Optimize routes
        if len(selected_vehicles) == 1:
            route_data = self.optimize_single_vehicle_route(selected_vehicles[0], selected_addresses)
            routes = [route_data]
        else:
            routes = self.optimize_multi_vehicle_routes(selected_vehicles, selected_addresses)
        
        # Calculate totals
        total_distance = sum(route['total_distance'] for route in routes)
        total_time = max(route['total_time'] for route in routes) if routes else 0
        total_cost = sum(route['total_cost'] for route in routes)
        
        optimization_time = time.time() - start_time
        
        return {
            'routes': routes,
            'total_distance': round(total_distance, 2),
            'total_time': total_time,
            'total_cost': round(total_cost, 2),
            'optimization_time': round(optimization_time, 3)
        }
