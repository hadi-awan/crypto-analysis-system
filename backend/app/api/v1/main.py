from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.auth import verify_token

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Protected endpoint example
@app.get("/api/performance/metrics")
async def get_performance_metrics(user_data: dict = Depends(verify_token)):
    user_id = user_data['user_id']
    # Get metrics for specific user
    return {"metrics": "data"}