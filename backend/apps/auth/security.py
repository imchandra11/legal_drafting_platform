import os
import time
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core import config, database, exceptions
from backend.apps.auth import schemas, models
from backend.utils import gdpr_utils

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/token",
    auto_error=False
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

def create_jwt_token(
    user_id: str,
    token_type: schemas.TokenType,
    expires_delta: timedelta = None
) -> str:
    """Create JWT token"""
    if not expires_delta:
        if token_type == schemas.TokenType.ACCESS:
            expires_delta = timedelta(minutes=config.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        else:
            expires_delta = timedelta(days=config.settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    expire = datetime.utcnow() + expires_delta
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": token_type.value
    }
    return jwt.encode(
        payload, 
        config.settings.JWT_SECRET,
        algorithm=config.settings.JWT_ALGORITHM
    )

def decode_jwt_token(token: str) -> schemas.TokenPayload:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(
            token,
            config.settings.JWT_SECRET,
            algorithms=[config.settings.JWT_ALGORITHM]
        )
        return schemas.TokenPayload(**payload)
    except JWTError as e:
        raise exceptions.InvalidCredentialsException from e

async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str
) -> models.User:
    """Authenticate user with email and password"""
    user = await models.User.get_by_email(db, email)
    if not user:
        raise exceptions.InvalidCredentialsException
    
    if not verify_password(password, user.hashed_password):
        raise exceptions.InvalidCredentialsException
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    return user

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(database.get_db)
) -> models.User:
    """Get current authenticated user from JWT token"""
    if not token:
        raise exceptions.InvalidCredentialsException
    
    try:
        payload = decode_jwt_token(token)
        if payload.type != schemas.TokenType.ACCESS:
            raise exceptions.InvalidCredentialsException
        
        user = await models.User.get(db, payload.sub)
        if not user:
            raise exceptions.InvalidCredentialsException
        
        return user
    except JWTError:
        raise exceptions.InvalidCredentialsException

async def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    return current_user

async def validate_password_reset_token(token: str) -> str:
    """Validate password reset token and return user ID"""
    try:
        payload = decode_jwt_token(token)
        if payload.type != schemas.TokenType.ACCESS:
            raise exceptions.InvalidCredentialsException
        return payload.sub
    except JWTError:
        raise exceptions.InvalidCredentialsException

def create_password_reset_token(email: str) -> str:
    """Create password reset token"""
    expires_delta = timedelta(minutes=config.settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {
            "sub": email,
            "exp": datetime.utcnow() + expires_delta,
            "type": "password_reset"
        },
        config.settings.JWT_SECRET,
        algorithm=config.settings.JWT_ALGORITHM
    )

def generate_secure_random(length: int = 32) -> str:
    """Generate secure random string"""
    return os.urandom(length).hex()

def get_oauth_login_url(provider: schemas.OAuthProvider) -> str:
    """Generate OAuth login URL for given provider"""
    if provider == schemas.OAuthProvider.GOOGLE:
        return (
            "https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={config.settings.GOOGLE_CLIENT_ID}&"
            "response_type=code&"
            f"redirect_uri={config.settings.OAUTH_REDIRECT_URI}&"
            "scope=openid%20email%20profile&"
            "access_type=offline"
        )
    elif provider == schemas.OAuthProvider.MICROSOFT:
        return (
            "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
            f"client_id={config.settings.MICROSOFT_CLIENT_ID}&"
            "response_type=code&"
            f"redirect_uri={config.settings.OAUTH_REDIRECT_URI}&"
            "scope=openid%20email%20profile&"
            "response_mode=query"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported OAuth provider"
        )