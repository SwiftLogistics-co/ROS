#!/usr/bin/env python3
"""
Test script for the coordinate-based route optimization endpoint
"""

import requests
import json
import time


def test_coordinate_optimization():
    """Test the coordinate optimization endpoint"""
    
    # Base URL for the API
    base_url = "http://localhost:8000/api/v1"
    endpoint = f"{base_url}/routes/optimize-coordinates"
    
    # Test data matching the user's requirement
    test_data = {
        "response": {
            "status": "success",
            "orders": {
                "order": [
                    {
                        "order_id": 1,
                        "address": "123 Main Street, Colombo 01",
                        "coordinate": {
                            "lat": 6.9271,
                            "lng": 79.8612
                        }
                    },
                    {
                        "order_id": 2,
                        "address": "456 Galle Road, Mount Lavinia",
                        "coordinate": {
                            "lat": 6.8389,
                            "lng": 79.8653
                        }
                    },
                    {
                        "order_id": 3,
                        "address": "789 Kandy Road, Kadawatha",
                        "coordinate": {
                            "lat": 7.0078,
                            "lng": 79.9553
                        }
                    },
                    {
                        "order_id": 4,
                        "address": "321 Negombo Road, Ja-Ela",
                        "coordinate": {
                            "lat": 7.0744,
                            "lng": 79.8947
                        }
                    },
                    {
                        "order_id": 5,
                        "address": "654 High Level Road, Nugegoda",
                        "coordinate": {
                            "lat": 6.8649,
                            "lng": 79.8997
                        }
                    }
                ]
            }
        }
    }
    
    print("Testing Coordinate-Based Route Optimization Endpoint")
    print("=" * 60)
    
    try:
        # Make the POST request
        print(f"Sending POST request to: {endpoint}")
        print(f"Payload: {json.dumps(test_data, indent=2)}")
        print("-" * 60)
        
        response = requests.post(
            endpoint,
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print("-" * 60)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS! Route optimization completed successfully.")
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Extract optimization summary
            summary = result.get('optimization_summary', {})
            print("\n📊 Optimization Summary:")
            print(f"  • Total Orders: {summary.get('total_orders', 'N/A')}")
            print(f"  • Total Distance: {summary.get('total_distance_km', 'N/A')} km")
            print(f"  • Algorithm: {summary.get('algorithm_used', 'N/A')}")
            
            # Show optimized order sequence
            optimized_orders = result.get('optimized_route', {}).get('orders', [])
            print("\n🚚 Optimized Route Sequence:")
            for i, order in enumerate(optimized_orders, 1):
                print(f"  {i}. Order ID {order['order_id']}: {order['address']}")
                print(f"     Coordinates: ({order['coordinate']['lat']}, {order['coordinate']['lng']})")
            
        else:
            print("❌ FAILED! Request failed.")
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Could not connect to the server.")
        print("Make sure the FastAPI server is running on localhost:8000")
        print("Run: python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {str(e)}")


def test_invalid_data():
    """Test the endpoint with invalid data"""
    
    base_url = "http://localhost:8000/api/v1"
    endpoint = f"{base_url}/routes/optimize-coordinates"
    
    print("\n" + "=" * 60)
    print("Testing Invalid Data Scenarios")
    print("=" * 60)
    
    # Test cases for invalid data
    test_cases = [
        {
            "name": "Empty Request",
            "data": {}
        },
        {
            "name": "Missing Orders",
            "data": {
                "response": {
                    "status": "success"
                }
            }
        },
        {
            "name": "Invalid Coordinate Format",
            "data": {
                "response": {
                    "status": "success",
                    "orders": {
                        "order": [
                            {
                                "order_id": 1,
                                "address": "123 Main Street",
                                "coordinate": {
                                    "lat": "invalid",
                                    "lng": 79.8612
                                }
                            }
                        ]
                    }
                }
            }
        }
    ]
    
    for test_case in test_cases:
        try:
            print(f"\nTesting: {test_case['name']}")
            response = requests.post(endpoint, json=test_case['data'])
            print(f"Status Code: {response.status_code}")
            
            if response.status_code != 200:
                error_detail = response.json()
                print(f"✅ Expected error: {error_detail.get('detail', 'Unknown error')}")
            else:
                print("❌ Unexpected success")
                
        except Exception as e:
            print(f"Error testing {test_case['name']}: {str(e)}")


if __name__ == "__main__":
    print("🚀 Starting Route Optimization Tests")
    test_coordinate_optimization()
    test_invalid_data()
    print("\n🏁 Testing completed!")
