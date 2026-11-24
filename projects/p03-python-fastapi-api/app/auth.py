"""Authentication module with JWT tokens and OAuth2 scopes."""

import hashlib
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from app.schemas import TokenData, UserResponse

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-dev-key-change-in-production-32bytes!")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token",
    scopes={
        "read:items": "Read items from catalog",
        "write:items": "Create and update items in catalog",
        "admin": "Administrative management and item deletion",
    },
)

# In-memory users database for demo/testing
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

FAKE_USERS_DB: Dict[str, dict] = {
    "alice": {
        "id": 1,
        "username": "alice",
        "email": "alice@example.com",
        "full_name": "Alice Engineer",
        "hashed_password": hash_password("alicepassword123"),
        "scopes": ["read:items", "write:items"],
        "is_active": True,
    },
    "admin_user": {
        "id": 2,
        "username": "admin_user",
        "email": "admin@example.com",
        "full_name": "System Administrator",
        "hashed_password": hash_password("adminpassword123"),
        "scopes": ["read:items", "write:items", "admin"],
        "is_active": True,
    },
    "readonly_user": {
        "id": 3,
        "username": "readonly_user",
        "email": "readonly@example.com",
        "full_name": "Read Only User",
        "hashed_password": hash_password("readonly123"),
        "scopes": ["read:items"],
        "is_active": True,
    },
}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": int(expire.timestamp()), "iat": int(now.timestamp())})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
) -> UserResponse:
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{ " ".join(security_scopes.scopes) }"'
    else:
        authenticate_value = "Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
    except jwt.PyJWTError:
        raise credentials_exception

    user = FAKE_USERS_DB.get(username)
    if user is None or not user.get("is_active"):
        raise credentials_exception

    # Enforce granular scope authorization
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions: missing required scope '{scope}'",
                headers={"WWW-Authenticate": authenticate_value},
            )

    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        full_name=user.get("full_name"),
        scopes=user.get("scopes", []),
        is_active=user["is_active"],
    )
