from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import math
from typing import List

app = FastAPI(
    title="Route Optimization API",
    version="1.0.0",
    description="Simple coordinate-based route optimization",
    docs_url="/docs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def calculate_distance(coord1: dict, coord2: dict) -> float:
    lat1, lon1 = math.radians(coord1["lat"]), math.radians(coord1["lng"])
    lat2, lon2 = math.radians(coord2["lat"]), math.radians(coord2["lng"])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return c * 6371

def optimize_route(orders: List[dict]) -> List[dict]:
    if not orders:
        return []
    optimized_route = [orders[0]]
    remaining = orders[1:]
    current = orders[0]["coordinate"]
    while remaining:
        nearest = min(remaining, key=lambda o: calculate_distance(current, o["coordinate"]))
        optimized_route.append(nearest)
        remaining.remove(nearest)
        current = nearest["coordinate"]
    return optimized_route

def calculate_total_distance(route: List[dict]) -> float:
    if len(route) < 2:
        return 0.0
    total = sum(calculate_distance(route[i]["coordinate"], route[i+1]["coordinate"]) for i in range(len(route)-1))
    return round(total, 2)

@app.get("/")
async def root():
    return {"message": "Route Optimization API", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/optimize-coordinates")
async def optimize(request: dict):
    try:
        if not request or "response" not in request:
            raise HTTPException(400, "Invalid request structure")
        orders = request["response"]["orders"]["order"]
        if not orders:
            raise HTTPException(400, "No orders provided")
        for order in orders:
            if not all(k in order for k in ["order_id", "address", "coordinate"]):
                raise HTTPException(400, "Invalid order structure")
            if not all(k in order["coordinate"] for k in ["lat", "lng"]):
                raise HTTPException(400, "Invalid coordinate structure")
        optimized = optimize_route(orders)
        distance = calculate_total_distance(optimized)
        return {
            "status": "success",
            "message": "Route optimized successfully",
            "optimization_summary": {
                "total_orders": len(optimized),
                "total_distance_km": distance,
                "algorithm_used": "nearest_neighbor"
            },
            "optimized_route": {"orders": optimized}
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Server error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
