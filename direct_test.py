"""
Direct test of the minimal optimizer functions
No API needed - just the core functions
"""

from minimal_optimizer import optimize_coordinates, get_coordinates

def main():
    print("🎯 Direct Route Optimization Test")
    print("=" * 40)
    
    # Test 1: Direct coordinates (fastest)
    print("Test 1: Using Direct Coordinates")
    coordinates = [
        (6.9338, 79.8501),  # Colombo Fort
        (6.9146, 79.8486),  # Liberty Plaza
        (6.9271, 79.8612),  # Crescat Boulevard
        (6.8387, 79.8635),  # Mount Lavinia
    ]
    
    print("Input coordinates:")
    for i, coord in enumerate(coordinates, 1):
        print(f"  {i}. {coord}")
    
    result = optimize_coordinates(coordinates)
    
    print("\n✅ Optimized Route:")
    for i, (coord, dist) in enumerate(zip(result["optimized_coordinates"], result["distances"]), 1):
        print(f"  {i}. {coord} - {dist} km")
    
    print(f"\n📊 Total Distance: {result['total_distance']} km")
    
    # Test 2: Address to coordinates (slower due to geocoding)
    print("\n" + "="*40)
    print("Test 2: Address to Coordinates")
    
    addresses = [
        "Colombo Fort, Sri Lanka",
        "Mount Lavinia, Sri Lanka"
    ]
    
    try:
        print("Getting coordinates for addresses:")
        coords_from_addresses = []
        for addr in addresses:
            coord = get_coordinates(addr)
            coords_from_addresses.append(coord)
            print(f"  {addr} -> {coord}")
        
        result2 = optimize_coordinates(coords_from_addresses)
        print(f"\n✅ Optimized distance: {result2['total_distance']} km")
        
    except Exception as e:
        print(f"❌ Geocoding error: {e}")
    
    # Test 3: Simple 2-point route
    print("\n" + "="*40) 
    print("Test 3: Simple 2-Point Route")
    
    simple_coords = [
        (6.9338, 79.8501),  # Start
        (6.8387, 79.8635),  # End
    ]
    
    simple_result = optimize_coordinates(simple_coords)
    print(f"Distance from start to end: {simple_result['total_distance']} km")
    
    print("\n🎉 All tests completed!")
    print("\n💡 To use in your code:")
    print("from minimal_optimizer import optimize_coordinates")
    print("coordinates = [(lat1, lon1), (lat2, lon2), ...]")
    print("result = optimize_coordinates(coordinates)")
    print("print(f'Total distance: {result[\"total_distance\"]} km')")

if __name__ == "__main__":
    main()
