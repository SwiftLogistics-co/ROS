from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Route Optimization API", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Route Optimization API is running!", "status": "success"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "Route Optimization System"}

@app.post("/test")
async def test_endpoint():
    return {"message": "Test endpoint working", "status": "success"}

if __name__ == "__main__":
    print("Starting Route Optimization API server...")
    print("Server will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
