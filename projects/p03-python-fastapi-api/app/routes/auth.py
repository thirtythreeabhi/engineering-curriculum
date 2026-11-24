"""Authentication routes: login, token issuance, and current user profile."""

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordRequestForm
from app.auth import FAKE_USERS_DB, create_access_token, get_current_user, hash_password
from app.schemas import TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = FAKE_USERS_DB.get(form_data.username)
    if not user or user["hashed_password"] != hash_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Honor requested scopes if subset of granted scopes, else grant user's scopes
    user_scopes = user.get("scopes", ["read:items"])
    requested_scopes = form_data.scopes if form_data.scopes else user_scopes
    effective_scopes = [s for s in requested_scopes if s in user_scopes]

    access_token = create_access_token(
        data={"sub": user["username"], "scopes": effective_scopes}
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=3600,
        scopes=effective_scopes,
    )


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: UserResponse = Security(get_current_user, scopes=["read:items"])
):
    return current_user
