from datetime import datetime, timedelta
from typing import Optional
import jwt
from app.core.config import get_settings

class JWTAuth:
    def __init__(self, secret_key: str = None):
        self.settings = get_settings()
        self.secret_key = secret_key or self.settings.JWT_SECRET_KEY
        self.algorithm = self.settings.JWT_ALGORITHM

    def create_token(self, user_id: int, expiration: Optional[timedelta] = None) -> str:
        if expiration is None:
            expiration = timedelta(minutes=self.settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
            
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + expiration,
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            return None

    def create_refresh_token(self, user_id: int) -> str:
        """Create a longer-lived refresh token"""
        expiration = timedelta(days=7)  # Refresh tokens typically live longer
        return self.create_token(user_id, expiration)