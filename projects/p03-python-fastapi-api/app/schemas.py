"""Pydantic v2 schemas with modern field validation and serializers."""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: str = Field(..., description="User email address")
    full_name: Optional[str] = Field(default=None, max_length=100)
    scopes: List[str] = Field(default_factory=lambda: ["read:items"])

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v.lower()


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password (at least 8 characters)")


class UserResponse(UserBase):
    id: int
    is_active: bool = True
    created_at: datetime = Field(default_factory=utc_now)

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    scopes: List[str]


class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = Field(default_factory=list)


class ItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = None
    price: float = Field(..., gt=0.0, description="Price must be strictly positive")
    stock: int = Field(default=0, ge=0, description="Stock must be non-negative")


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = None
    price: Optional[float] = Field(default=None, gt=0.0)
    stock: Optional[int] = Field(default=None, ge=0)


class ItemResponse(ItemBase):
    id: int
    created_at: datetime = Field(default_factory=utc_now)

    model_config = {"from_attributes": True}
