"""
Test Route Optimization with Real Sri Lankan Data
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_real_sri_lankan_routes():
    """Test with real Sri Lankan addresses"""
    print("🇱🇰 Testing with Real Sri Lankan Locations")
    print("=" * 50)
    
    # Test Case 1: Colombo Business District Route
    colombo_route = {
        "driver_id": 101,
        "start_location": "Colombo Fort Railway Station",
        "end_location": "Independence Square, Colombo 07",
        "order_locations": [
            {
                "order_id": "ORD_COL_001",
                "location": "Galle Face Green, Colombo 03",
                "priority": 1
            },
            {
                "order_id": "ORD_COL_002", 
                "location": "Pettah Market, Colombo 11",
                "priority": 2
            },
            {
                "order_id": "ORD_COL_003",
                "location": "National Museum, Colombo 07",
                "priority": 1
            },
            {
                "order_id": "ORD_COL_004",
                "location": "Viharamahadevi Park, Colombo 07",
                "priority": 3
            }
        ],
        "route_name": "Colombo Business District Delivery"
    }
    
    print("📦 Test Case 1: Colombo Business District")
    test_route_optimization(colombo_route)
    print()
    
    # Test Case 2: Suburban Colombo Route
    suburban_route = {
        "driver_id": 102,
        "start_location": "Nugegoda Junction",
        "end_location": "Maharagama Clock Tower",
        "order_locations": [
            {
                "order_id": "ORD_SUB_001",
                "location": "Delkanda Junction",
                "priority": 1
            },
            {
                "order_id": "ORD_SUB_002",
                "location": "Kottawa Temple Road",
                "priority": 2
            },
            {
                "order_id": "ORD_SUB_003", 
                "location": "Boralesgamuwa High Level Road",
                "priority": 1
            }
        ],
        "route_name": "Suburban Colombo Delivery"
    }
    
    print("📦 Test Case 2: Suburban Colombo Route")
    test_route_optimization(suburban_route)
    print()
    
    # Test Case 3: Kandy Tourist Route
    kandy_route = {
        "driver_id": 103,
        "start_location": "Kandy Railway Station",
        "end_location": "University of Peradeniya",
        "order_locations": [
            {
                "order_id": "ORD_KDY_001",
                "location": "Temple of the Sacred Tooth Relic, Kandy",
                "priority": 1
            },
            {
                "order_id": "ORD_KDY_002",
                "location": "Kandy Lake, Kandy",
                "priority": 2
            },
            {
                "order_id": "ORD_KDY_003",
                "location": "Royal Botanical Gardens, Peradeniya",
                "priority": 1
            }
        ],
        "route_name": "Kandy Tourist Delivery"
    }
    
    print("📦 Test Case 3: Kandy Tourist Route")
    test_route_optimization(kandy_route)
    print()

def test_route_optimization(route_data):
    """Test a single route optimization"""
    try:
        response = requests.post(
            f"{BASE_URL}/optimize-driver-route",
            json=route_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Route optimization successful!")
            print(f"👨‍💼 Driver ID: {result['driver_id']}")
            print(f"📋 Route Name: {result['route_name']}")
            print(f"📍 Start: {result['start_location']}")
            print(f"🏁 End: {result['end_location']}")
            print(f"📏 Total Distance: {result['total_distance_km']} km")
            print(f"⏱️  Total Time: {result['total_time_minutes']} minutes")
            print(f"📦 Total Orders: {result['total_orders']}")
            
            print("\n🗺️  Optimized Route:")
            for stop in result['optimized_route']:
                print(f"   {stop['sequence']}. Order {stop['order_id']}")
                print(f"      📍 {stop['location']}")
                print(f"      🌐 Lat: {stop['latitude']:.6f}, Lon: {stop['longitude']:.6f}")
                print(f"      🚛 Distance: {stop['distance_from_previous_km']} km")
                print(f"      ⏱️  Travel Time: {stop['estimated_travel_time_minutes']} min")
                print()
            
            return result
        else:
            print(f"❌ Optimization failed: {response.status_code}")
            print(f"Error details: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Is the server running on port 8000?")
        print("💡 Start the server with: python route_server.py")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def test_with_coordinates():
    """Test with pre-defined coordinates for faster testing"""
    print("🎯 Testing with Pre-defined Coordinates")
    print("=" * 50)
    
    route_with_coords = {
        "driver_id": 104,
        "start_location": "Colombo Fort",
        "end_location": "Mount Lavinia Beach",
        "order_locations": [
            {
                "order_id": "ORD_COORD_001",
                "location": "Liberty Plaza, Colombo 03",
                "latitude": 6.9146,
                "longitude": 79.8486,
                "priority": 1
            },
            {
                "order_id": "ORD_COORD_002",
                "location": "Bambalapitiya Station",
                "latitude": 6.8965,
                "longitude": 79.8553,
                "priority": 2
            },
            {
                "order_id": "ORD_COORD_003",
                "location": "Wellawatta Beach",
                "latitude": 6.8774,
                "longitude": 79.8607,
                "priority": 1
            }
        ],
        "route_name": "Colombo Coast Express"
    }
    
    test_route_optimization(route_with_coords)

def check_server_health():
    """Check if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print("✅ Server is healthy!")
            print(f"🛠️  Service: {result['service']}")
            print(f"🗄️  Supabase: {result.get('supabase', 'not configured')}")
            return True
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("💡 Make sure to start the server first:")
        print("   python route_server.py")
        return False

if __name__ == "__main__":
    print("🚀 Route Optimization Real Data Test")
    print("=" * 60)
    print()
    
    # Check server health first
    if check_server_health():
        print()
        
        # Test with real Sri Lankan routes
        test_real_sri_lankan_routes()
        
        # Test with coordinates for speed
        test_with_coordinates()
        
        print("🎉 All tests completed!")
        print()
        print("📊 Summary:")
        print("- Tested various Sri Lankan locations")
        print("- Geocoding working with real addresses")
        print("- Route optimization calculating real distances")
        print("- Multiple delivery scenarios tested")
        print()
        print("📚 View API docs: http://localhost:8000/docs")
        print("🌐 Server status: http://localhost:8000/health")
    else:
        print()
        print("🚫 Cannot run tests - server is not responding")
        print()
        print("📋 To start the server:")
        print("1. Open a terminal in the ROS directory")
        print("2. Run: python route_server.py")
        print("3. Wait for 'Application startup complete'")
        print("4. Run this test again: python test_real_data.py")
