"""
Test Route Optimization with CSV Data and Performance Metrics
"""

import requests
import json
import time
import csv
from datetime import datetime
import statistics

BASE_URL = "http://localhost:8000"

def create_sample_csv_data():
    """Create sample CSV files with Sri Lankan delivery data"""
    print("📄 Creating sample CSV data files...")
    
    # Create orders CSV
    orders_data = [
        ["order_id", "customer_name", "address", "phone", "priority", "delivery_date"],
        ["ORD_CSV_001", "Kamal Perera", "Reid Avenue, Colombo 07", "0771234567", 1, "2025-09-09"],
        ["ORD_CSV_002", "Nimal Silva", "Galle Road, Mount Lavinia", "0772345678", 2, "2025-09-09"],
        ["ORD_CSV_003", "Priya Fernando", "Kandy Road, Maharagama", "0773456789", 1, "2025-09-09"],
        ["ORD_CSV_004", "Sunil Jayawardena", "High Level Road, Nugegoda", "0774567890", 3, "2025-09-09"],
        ["ORD_CSV_005", "Malini Wijesinghe", "Baseline Road, Colombo 09", "0775678901", 1, "2025-09-09"],
        ["ORD_CSV_006", "Chaminda Raj", "Duplication Road, Colombo 04", "0776789012", 2, "2025-09-09"],
        ["ORD_CSV_007", "Sanduni Kumari", "Marine Drive, Colombo 03", "0777890123", 1, "2025-09-09"],
        ["ORD_CSV_008", "Ruwan Perera", "Flower Road, Colombo 07", "0778901234", 2, "2025-09-09"],
        ["ORD_CSV_009", "Dilani Mendis", "Union Place, Colombo 02", "0779012345", 1, "2025-09-09"],
        ["ORD_CSV_010", "Tharaka Silva", "Parliament Road, Kotte", "0770123456", 3, "2025-09-09"]
    ]
    
    with open("sample_orders.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(orders_data)
    
    # Create drivers CSV
    drivers_data = [
        ["driver_id", "driver_name", "vehicle_type", "capacity", "start_location"],
        [401, "Anil Bandara", "Van", 20, "Colombo Fort"],
        [402, "Piyal Gunasekara", "Truck", 50, "Pettah Market"],
        [403, "Roshan Perera", "Three Wheeler", 5, "Nugegoda Junction"],
        [404, "Lasith Fernando", "Motorbike", 3, "Mount Lavinia"],
        [405, "Saman Wijeratne", "Car", 8, "Maharagama"]
    ]
    
    with open("sample_drivers.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(drivers_data)
    
    print("✅ Created sample_orders.csv and sample_drivers.csv")
    return True

def load_csv_data():
    """Load order and driver data from CSV files"""
    try:
        # Load orders
        orders = []
        with open("sample_orders.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                orders.append({
                    "order_id": row["order_id"],
                    "location": row["address"],
                    "priority": int(row["priority"])
                })
        
        # Load drivers
        drivers = []
        with open("sample_drivers.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                drivers.append({
                    "driver_id": int(row["driver_id"]),
                    "driver_name": row["driver_name"],
                    "vehicle_type": row["vehicle_type"],
                    "start_location": row["start_location"]
                })
        
        print(f"📊 Loaded {len(orders)} orders and {len(drivers)} drivers from CSV")
        return orders, drivers
        
    except FileNotFoundError:
        print("❌ CSV files not found. Creating sample data...")
        create_sample_csv_data()
        return load_csv_data()
    except Exception as e:
        print(f"❌ Error loading CSV data: {e}")
        return [], []

def test_csv_route_optimization():
    """Test route optimization using CSV data"""
    print("📊 Testing Route Optimization with CSV Data")
    print("=" * 60)
    
    orders, drivers = load_csv_data()
    
    if not orders or not drivers:
        print("❌ No data available for testing")
        return
    
    # Test with different drivers and order combinations
    test_results = []
    
    for driver in drivers[:3]:  # Test with first 3 drivers
        # Create different order sets
        order_sets = [
            orders[:3],    # First 3 orders
            orders[3:6],   # Next 3 orders
            orders[6:9],   # Last 3 orders
        ]
        
        for i, order_set in enumerate(order_sets, 1):
            print(f"🚚 Testing Driver {driver['driver_id']} ({driver['driver_name']}) - Set {i}")
            
            route_data = {
                "driver_id": driver["driver_id"],
                "start_location": driver["start_location"],
                "end_location": "Colombo Port",  # Common end point
                "order_locations": order_set,
                "route_name": f"CSV_Route_{driver['driver_id']}_Set_{i}"
            }
            
            # Measure performance
            start_time = time.time()
            
            try:
                response = requests.post(
                    f"{BASE_URL}/optimize-driver-route",
                    json=route_data,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    test_results.append({
                        "driver_id": driver["driver_id"],
                        "driver_name": driver["driver_name"],
                        "vehicle_type": driver["vehicle_type"],
                        "orders_count": len(order_set),
                        "total_distance": result["total_distance_km"],
                        "total_time": result["total_time_minutes"],
                        "processing_time": processing_time,
                        "status": "success"
                    })
                    
                    print(f"   ✅ Success! Distance: {result['total_distance_km']} km")
                    print(f"   ⏱️  Processing Time: {processing_time:.2f} seconds")
                    print(f"   📦 Orders: {result['total_orders']}")
                else:
                    test_results.append({
                        "driver_id": driver["driver_id"],
                        "status": "failed",
                        "error": response.status_code
                    })
                    print(f"   ❌ Failed: {response.status_code}")
                    
            except Exception as e:
                test_results.append({
                    "driver_id": driver["driver_id"],
                    "status": "error",
                    "error": str(e)
                })
                print(f"   ❌ Error: {e}")
            
            print()
    
    # Generate performance report
    generate_performance_report(test_results)

def generate_performance_report(test_results):
    """Generate performance analysis report"""
    print("📈 Performance Analysis Report")
    print("=" * 50)
    
    successful_tests = [r for r in test_results if r.get("status") == "success"]
    
    if not successful_tests:
        print("❌ No successful tests to analyze")
        return
    
    # Calculate statistics
    processing_times = [r["processing_time"] for r in successful_tests]
    distances = [r["total_distance"] for r in successful_tests]
    times = [r["total_time"] for r in successful_tests]
    
    print(f"✅ Successful Tests: {len(successful_tests)}/{len(test_results)}")
    print(f"⚡ Average Processing Time: {statistics.mean(processing_times):.2f} seconds")
    print(f"📏 Average Route Distance: {statistics.mean(distances):.2f} km")
    print(f"⏱️  Average Route Time: {statistics.mean(times):.1f} minutes")
    print()
    
    # Vehicle type analysis
    vehicle_performance = {}
    for result in successful_tests:
        vehicle_type = result["vehicle_type"]
        if vehicle_type not in vehicle_performance:
            vehicle_performance[vehicle_type] = []
        vehicle_performance[vehicle_type].append(result)
    
    print("🚗 Performance by Vehicle Type:")
    for vehicle_type, results in vehicle_performance.items():
        avg_distance = statistics.mean([r["total_distance"] for r in results])
        avg_time = statistics.mean([r["processing_time"] for r in results])
        print(f"   {vehicle_type}: Avg Distance {avg_distance:.2f} km, Avg Processing {avg_time:.2f}s")
    
    print()
    
    # Save detailed results to CSV
    save_results_to_csv(test_results)

def save_results_to_csv(test_results):
    """Save test results to CSV file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"route_optimization_results_{timestamp}.csv"
    
    try:
        with open(filename, "w", newline="", encoding="utf-8") as f:
            if test_results:
                writer = csv.DictWriter(f, fieldnames=test_results[0].keys())
                writer.writeheader()
                writer.writerows(test_results)
        
        print(f"💾 Results saved to: {filename}")
    except Exception as e:
        print(f"❌ Error saving results: {e}")

def test_api_load():
    """Test API performance under load"""
    print("🔥 API Load Testing")
    print("=" * 30)
    
    # Simple route for load testing
    simple_route = {
        "driver_id": 999,
        "start_location": "Colombo Fort",
        "end_location": "Mount Lavinia",
        "order_locations": [
            {"order_id": f"LOAD_TEST_001", "location": "Galle Road, Colombo 03", "priority": 1},
            {"order_id": f"LOAD_TEST_002", "location": "Marine Drive, Colombo 03", "priority": 1}
        ],
        "route_name": "Load Test Route"
    }
    
    num_requests = 10
    response_times = []
    successful_requests = 0
    
    print(f"🚀 Sending {num_requests} concurrent requests...")
    
    for i in range(num_requests):
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{BASE_URL}/optimize-driver-route",
                json=simple_route,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            response_times.append(response_time)
            
            if response.status_code == 200:
                successful_requests += 1
                
        except Exception as e:
            print(f"   Request {i+1} failed: {e}")
    
    # Load test results
    if response_times:
        print(f"✅ Successful Requests: {successful_requests}/{num_requests}")
        print(f"⚡ Average Response Time: {statistics.mean(response_times):.2f} seconds")
        print(f"🚀 Fastest Response: {min(response_times):.2f} seconds")
        print(f"🐌 Slowest Response: {max(response_times):.2f} seconds")
    else:
        print("❌ No successful responses recorded")

if __name__ == "__main__":
    print("📊 Route Optimization CSV & Performance Testing")
    print("=" * 70)
    print()
    
    # Check server health
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            print()
            
            # Create sample data and test
            test_csv_route_optimization()
            print()
            
            # Load testing
            test_api_load()
            print()
            
            print("🎉 All CSV and performance tests completed!")
            print()
            print("📁 Generated files:")
            print("- sample_orders.csv")
            print("- sample_drivers.csv") 
            print("- route_optimization_results_*.csv")
            
        else:
            print("❌ Server not responding")
            
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("💡 Start the server: python route_server.py")
