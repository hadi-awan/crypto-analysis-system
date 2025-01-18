from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from typing import Optional
from config import settings

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = security) -> dict:
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=['HS256']
        )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=403,
            detail="Invalid authentication credentials"
        )

# api-service/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from middleware.auth import verify_token

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