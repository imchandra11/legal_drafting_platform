from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum

class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    current_password: Optional[str] = None
    new_password: Optional[str] = None

class UserInDB(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: str  # User ID
    exp: int
    type: TokenType

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class OAuthProvider(str, Enum):
    GOOGLE = "google"
    MICROSOFT = "microsoft"

class OAuthToken(BaseModel):
    provider: OAuthProvider
    access_token: str
    id_token: Optional[str] = None