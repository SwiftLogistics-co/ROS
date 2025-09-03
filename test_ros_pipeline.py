"""
ROS Pipeline Test Script
Demonstrates the complete Route Optimization System pipeline
"""

import asyncio
import json
from app.services.ros_pipeline import ROSPipelineService
from app.db.models import Vehicle, Address


def create_test_vehicle():
    """Create a test vehicle"""
    return Vehicle(
        id=1,
        name="Delivery Van 1",
        vehicle_type="van",
        capacity=1000.0,
        max_distance=200.0,
        cost_per_km=0.5,
        start_location="Downtown Depot, Springfield, IL",
        is_available=True
    )


def create_test_addresses():
    """Create test delivery addresses"""
    addresses = [
        Address(
            id=1,
            name="Customer A",
            street_address="123 Oak Street",
            city="Springfield",
            state="IL",
            postal_code="62701",
            country="USA",
            delivery_weight=15.0,
            delivery_volume=8.0,
            service_time=10,
            priority=2
        ),
        Address(
            id=2,
            name="Customer B", 
            street_address="456 Maple Avenue",
            city="Springfield",
            state="IL",
            postal_code="62702",
            country="USA",
            delivery_weight=25.0,
            delivery_volume=12.0,
            service_time=15,
            priority=1
        ),
        Address(
            id=3,
            name="Customer C",
            street_address="789 Pine Road",
            city="Springfield", 
            state="IL",
            postal_code="62703",
            country="USA",
            delivery_weight=8.0,
            delivery_volume=5.0,
            service_time=20,
            priority=3
        ),
        Address(
            id=4,
            name="Customer D",
            street_address="321 Elm Street",
            city="Springfield",
            state="IL", 
            postal_code="62704",
            country="USA",
            delivery_weight=30.0,
            delivery_volume=18.0,
            service_time=12,
            priority=2
        )
    ]
    return addresses


async def test_ros_pipeline():
    """Test the complete ROS pipeline"""
    print("🚚 ROS Pipeline Test Starting...")
    print("=" * 50)
    
    # Initialize ROS pipeline
    ros_pipeline = ROSPipelineService()
    
    # Create test data
    vehicle = create_test_vehicle()
    addresses = create_test_addresses()
    
    print(f"📋 Test Setup:")
    print(f"   Vehicle: {vehicle.name} (Capacity: {vehicle.capacity}kg)")
    print(f"   Addresses: {len(addresses)} delivery locations")
    print()
    
    try:
        # Run the complete ROS pipeline
        print("🔄 Running ROS Pipeline...")
        result = await ros_pipeline.process_optimization_request([vehicle], addresses)
        
        if "error" in result:
            print(f"❌ Pipeline failed: {result['error']}")
            return
        
        # Display results
        print("✅ Pipeline completed successfully!")
        print()
        print("📊 Optimization Results:")
        print("-" * 30)
        print(f"   Optimization Engine: {result.get('optimization_engine', 'Fallback')}")
        print(f"   Geocoded Addresses: {result.get('geocoded_addresses', 0)}/{len(addresses)}")
        print(f"   Total Distance: {result['total_distance']} km")
        print(f"   Total Time: {result['total_time']} minutes")
        print(f"   Total Cost: ${result['total_cost']:.2f}")
        print(f"   Optimization Time: {result['optimization_time']:.3f} seconds")
        print()
        
        # Display route details
        for i, route in enumerate(result['routes'], 1):
            print(f"🚐 Route {i} (Vehicle {route['vehicle_id']}):")
            print(f"   Distance: {route['total_distance']} km")
            print(f"   Time: {route['total_time']} minutes") 
            print(f"   Cost: ${route['total_cost']:.2f}")
            print(f"   Stops: {len(route['stops'])}")
            
            for j, stop in enumerate(route['stops'], 1):
                address = next(a for a in addresses if a.id == stop['address_id'])
                print(f"     {j}. {address.name} ({address.street_address})")
                print(f"        Arrival: {stop['estimated_arrival']}")
                print(f"        Distance from previous: {stop['distance_from_previous']:.1f} km")
            print()
    
    except Exception as e:
        print(f"❌ Pipeline error: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_geocoding_only():
    """Test just the geocoding step"""
    print("🗺️  Testing Geocoding Service...")
    print("=" * 40)
    
    ros_pipeline = ROSPipelineService()
    addresses = create_test_addresses()
    
    print("📍 Geocoding addresses...")
    coordinates = ros_pipeline.geocoding_service.batch_geocode_addresses(addresses)
    
    print("Geocoding Results:")
    for address in addresses:
        coords = coordinates.get(address.id, (0.0, 0.0))
        status = "✅ Success" if coords != (0.0, 0.0) else "❌ Failed"
        print(f"   {address.name}: {coords[0]:.6f}, {coords[1]:.6f} {status}")


if __name__ == "__main__":
    print("ROS (Route Optimization System) Pipeline Test")
    print("=" * 50)
    print()
    
    # Test geocoding first
    print("Step 1: Testing Geocoding...")
    asyncio.run(test_geocoding_only())
    print()
    
    # Test complete pipeline
    print("Step 2: Testing Complete Pipeline...")
    asyncio.run(test_ros_pipeline())
    
    print()
    print("🎉 Test completed!")
    print()
    print("Next steps:")
    print("1. Start the FastAPI server: uvicorn app.main:app --reload")
    print("2. Open http://localhost:8000/docs for API documentation")
    print("3. Use the /api/v1/ros/optimize-advanced endpoint for production optimization")
