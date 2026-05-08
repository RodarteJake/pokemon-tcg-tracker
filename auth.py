import bcrypt
from fastapi import HTTPException, Cookie
import jwt
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import db

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable is required")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "60"))

def hash_password(password: str) -> str:
    """Hash a password using bcrypt adding a salt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hashed value."""
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_access_token(user_id: int) -> str:
    """Create a JWT access token for a given user ID."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=JWT_EXPIRY_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str) -> int | None:
    """Decode a JWT access token and return the user ID, or None if invalid."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return int(payload["sub"])
    except jwt.InvalidTokenError:
        return None
    
def get_current_user(access_token: str | None = Cookie(default=None)) -> int:
    """FastAPI dependency: returns the authenticated user_id, or raises 401."""
    if access_token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = decode_access_token(access_token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Verify the user still exists (they could have been deleted while token is valid)
    if db.get_user_by_id(user_id) is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user_id

def get_optional_user(access_token: str | None = Cookie(default=None)) -> int | None:
    """FastAPI dependency: returns the authenticated user_id, or None if not authenticated."""
    if access_token is None:
        return None
    
    user_id = decode_access_token(access_token)
    if user_id is None:
        return None
    
    # Verify the user still exists (they could have been deleted while token is valid)
    if db.get_user_by_id(user_id) is None:
        return None
    
    return user_id
