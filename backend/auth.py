import jwt
import os
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from fastapi import HTTPException, Header

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__truncate_error=False)

# JWT secret key — in production, use a secure random key from env
JWT_SECRET = os.getenv("JWT_SECRET", "ai-hub-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

# =========================
# PYDANTIC MODELS
# =========================

class SignupRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    token: str
    username: str

# =========================
# PASSWORD UTILITIES
# =========================

def hash_password(password: str) -> str:
    # Bcrypt has a 72-byte limit. We truncate to 72 characters to prevent errors.
    return pwd_context.hash(password[:72])

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# =========================
# JWT UTILITIES
# =========================

def create_token(user_id: int, username: str) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# =========================
# AUTH DEPENDENCY
# =========================

async def get_current_user(authorization: str = Header(None)):
    """FastAPI dependency to extract and validate the JWT from the Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    return payload
