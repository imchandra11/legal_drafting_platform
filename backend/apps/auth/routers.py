from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from backend.core.database import get_db
from backend.core import config, exceptions
from backend.apps.auth import schemas, security, models
from backend.utils.email import send_password_reset_email
from .dependencies import validate_oauth_token

router = APIRouter()

@router.post("/register", response_model=schemas.UserInDB)
async def register_user(
    user_data: schemas.UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    existing_user = await models.User.get_by_email(db, user_data.email)
    if existing_user:
        raise exceptions.InvalidCredentialsException
    
    hashed_password = security.get_password_hash(user_data.password)
    user = await models.User.create(db, {
        "email": user_data.email,
        "full_name": user_data.full_name,
        "hashed_password": hashed_password
    })
    return user

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return access/refresh tokens"""
    user = await security.authenticate_user(db, form_data.username, form_data.password)
    await user.update_last_login(db)
    
    access_token = security.create_jwt_token(
        str(user.id),
        schemas.TokenType.ACCESS
    )
    refresh_token = security.create_jwt_token(
        str(user.id),
        schemas.TokenType.REFRESH
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=schemas.Token)
async def refresh_access_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    try:
        payload = security.decode_jwt_token(refresh_token)
        if payload.type != schemas.TokenType.REFRESH:
            raise exceptions.InvalidCredentialsException
        
        user = await models.User.get(db, payload.sub)
        if not user:
            raise exceptions.InvalidCredentialsException
        
        new_access_token = security.create_jwt_token(
            str(user.id),
            schemas.TokenType.ACCESS
        )
        return {
            "access_token": new_access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except JWTError:
        raise exceptions.InvalidCredentialsException

@router.get("/me", response_model=schemas.UserInDB)
async def get_current_user(
    current_user: models.User = Depends(security.get_current_active_user),
):
    """Get current authenticated user"""
    return current_user

@router.post("/password-reset-request")
async def request_password_reset(
    reset_request: schemas.PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
    request: Request
):
    """Request password reset email"""
    user = await models.User.get_by_email(db, reset_request.email)
    if not user:
        # Don't reveal if user exists for security
        return {"detail": "If the email exists, a reset link has been sent"}
    
    reset_token = security.create_password_reset_token(reset_request.email)
    reset_url = f"{request.base_url}api/auth/password-reset?token={reset_token}"
    
    await send_password_reset_email(
        email=user.email,
        name=user.full_name or "User",
        reset_url=reset_url
    )
    
    return {"detail": "If the email exists, a reset link has been sent"}

@router.post("/password-reset")
async def confirm_password_reset(
    reset_data: schemas.PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """Confirm password reset with token"""
    try:
        # Validate token
        email = jwt.decode(
            reset_data.token,
            config.settings.JWT_SECRET,
            algorithms=[config.settings.JWT_ALGORITHM]
        )["sub"]
        
        user = await models.User.get_by_email(db, email)
        if not user:
            raise exceptions.InvalidCredentialsException
        
        # Update password
        hashed_password = security.get_password_hash(reset_data.new_password)
        await models.User.update(db, user.id, {
            "hashed_password": hashed_password
        })
        
        return {"detail": "Password has been reset successfully"}
    except JWTError:
        raise exceptions.InvalidCredentialsException

@router.post("/oauth/{provider}/login")
async def oauth_login(
    provider: schemas.OAuthProvider,
):
    """Initiate OAuth login flow"""
    login_url = security.get_oauth_login_url(provider)
    return {"authorization_url": login_url}

@router.post("/oauth/{provider}/callback")
async def oauth_callback(
    provider: schemas.OAuthProvider,
    oauth_token: schemas.OAuthToken = Depends(validate_oauth_token),
    db: AsyncSession = Depends(get_db)
):
    """Handle OAuth callback and authenticate user"""
    # Validate token and get user info
    user_info = await security.get_oauth_user_info(provider, oauth_token)
    
    # Get or create user
    user = await models.User.get_or_create_oauth_user(
        db,
        email=user_info["email"],
        oauth_provider=provider.value,
        oauth_id=user_info["sub"],
        full_name=user_info.get("name")
    )
    
    # Generate tokens
    access_token = security.create_jwt_token(
        str(user.id),
        schemas.TokenType.ACCESS
    )
    refresh_token = security.create_jwt_token(
        str(user.id),
        schemas.TokenType.REFRESH
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    current_user: models.User = Depends(security.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """GDPR-compliant account deletion"""
    await gdpr_utils.anonymize_user_data(str(current_user.id), db)
    return None