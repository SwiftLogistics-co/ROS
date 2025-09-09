"""
Minimal Route Optimizer - Input coordinates, get optimized route
"""

from geopy.distance import geodesic
from typing import List, Tuple, Dict

def optimize_coordinates(coordinates: List[Tuple[float, float]]) -> Dict:
    """
    Takes list of coordinates and returns optimized route
    
    Args:
        coordinates: List of (latitude, longitude) tuples
        First = start, Last = end, Middle = optimize
    
    Returns:
        {
            "optimized_coordinates": [(lat, lon), ...],
            "distances": [0, dist1, dist2, ...], 
            "total_distance": total_km
        }
    """
    if len(coordinates) < 2:
        return {"error": "Need at least 2 coordinates"}
    
    if len(coordinates) == 2:
        # Just start and end
        distance = geodesic(coordinates[0], coordinates[1]).kilometers
        return {
            "optimized_coordinates": coordinates,
            "distances": [0, round(distance, 2)],
            "total_distance": round(distance, 2)
        }
    
    # Optimize middle points using nearest neighbor
    start = coordinates[0]
    end = coordinates[-1]
    middle_points = coordinates[1:-1]
    
    # Build optimized route
    optimized = [start]
    current_pos = start
    remaining = middle_points[:]
    distances = [0]
    total_distance = 0
    
    # Find nearest neighbor for each step
    while remaining:
        nearest_idx = 0
        min_distance = geodesic(current_pos, remaining[0]).kilometers
        
        for i, point in enumerate(remaining[1:], 1):
            distance = geodesic(current_pos, point).kilometers
            if distance < min_distance:
                min_distance = distance
                nearest_idx = i
        
        # Add nearest point to route
        nearest_point = remaining.pop(nearest_idx)
        optimized.append(nearest_point)
        distances.append(round(min_distance, 2))
        total_distance += min_distance
        current_pos = nearest_point
    
    # Add final distance to end
    final_distance = geodesic(current_pos, end).kilometers
    optimized.append(end)
    distances.append(round(final_distance, 2))
    total_distance += final_distance
    
    return {
        "optimized_coordinates": optimized,
        "distances": distances,
        "total_distance": round(total_distance, 2)
    }

def get_coordinates(address: str) -> Tuple[float, float]:
    """Helper function to get coordinates for an address"""
    from geopy.geocoders import Nominatim
    
    geocoder = Nominatim(user_agent="SimpleRoute", timeout=10)
    try:
        location = geocoder.geocode(address)
        if location:
            return (location.latitude, location.longitude)
        else:
            raise ValueError(f"Address not found: {address}")
    except Exception as e:
        raise ValueError(f"Geocoding error: {e}")

# Example usage
if __name__ == "__main__":
    print("📍 Minimal Route Optimizer")
    print("=" * 30)
    
    # Example 1: Direct coordinates
    print("Example 1: Direct Coordinates")
    test_coordinates = [
        (6.9338, 79.8501),  # Colombo Fort
        (6.9146, 79.8486),  # Liberty Plaza  
        (6.9271, 79.8612),  # Crescat Boulevard
        (6.8387, 79.8635),  # Mount Lavinia
    ]
    
    result = optimize_coordinates(test_coordinates)
    
    print("Input coordinates:")
    for i, coord in enumerate(test_coordinates):
        print(f"  {i+1}. {coord}")
    
    print("\nOptimized route:")
    for i, (coord, dist) in enumerate(zip(result["optimized_coordinates"], result["distances"])):
        print(f"  {i+1}. {coord} - {dist} km")
    
    print(f"\nTotal Distance: {result['total_distance']} km")
    
    # Example 2: With address lookup
    print("\n" + "="*40)
    print("Example 2: Address to Coordinates")
    
    addresses = [
        "Colombo Fort, Sri Lanka",
        "Galle Road, Colombo, Sri Lanka",
        "Mount Lavinia, Sri Lanka"
    ]
    
    try:
        coords_from_addresses = []
        print("Getting coordinates:")
        for addr in addresses:
            coord = get_coordinates(addr)
            coords_from_addresses.append(coord)
            print(f"  {addr} -> {coord}")
        
        result2 = optimize_coordinates(coords_from_addresses)
        print(f"\nOptimized total distance: {result2['total_distance']} km")
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n✨ Usage:")
    print("coordinates = [(lat1, lon1), (lat2, lon2), ...]")
    print("result = optimize_coordinates(coordinates)")
    print("print(result['total_distance'])")
