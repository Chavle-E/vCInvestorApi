from pydantic import BaseModel, EmailStr
from typing import Optional


class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    subscription_tier: str
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None


class TokenPayload(BaseModel):
    sub: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
