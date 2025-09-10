import requests
import json

def test_api():
    url = "http://localhost:8000/optimize-coordinates"
    data = {
        "response": {
            "status": "success",
            "orders": {
                "order": [
                    {"order_id": 1, "address": "123 Main St, Colombo", "coordinate": {"lat": 6.9271, "lng": 79.8612}},
                    {"order_id": 2, "address": "456 Galle Rd, Mount Lavinia", "coordinate": {"lat": 6.8389, "lng": 79.8653}},
                    {"order_id": 3, "address": "789 Kandy Rd, Kadawatha", "coordinate": {"lat": 7.0078, "lng": 79.9553}},
                    {"order_id": 4, "address": "321 Negombo Rd, Ja-Ela", "coordinate": {"lat": 7.0744, "lng": 79.8947}},
                    {"order_id": 5, "address": "654 High Level Rd, Nugegoda", "coordinate": {"lat": 6.8649, "lng": 79.8997}}
                ]
            }
        }
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"📊 Orders: {result[\"optimization_summary\"][\"total_orders\"]}")
            print(f"📏 Distance: {result[\"optimization_summary\"][\"total_distance_km\"]} km")
            print("🚚 Route:")
            for i, order in enumerate(result[\"optimized_route\"][\"orders\"], 1):
                print(f"  {i}. Order {order[\"order_id\"]}: {order[\"address\"]}")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api()
