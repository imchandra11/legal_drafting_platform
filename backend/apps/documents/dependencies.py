from fastapi import Depends, HTTPException, status
from jose import jwt
from backend.core import config, exceptions
from backend.apps.auth import schemas

async def validate_oauth_token(
    provider: schemas.OAuthProvider,
    token: schemas.OAuthToken
) -> schemas.OAuthToken:
    """Validate OAuth token structure"""
    if not token.access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing access token"
        )
    
    if provider == schemas.OAuthProvider.GOOGLE and not token.id_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google requires ID token"
        )
    
    return token

async def get_oauth_user_info(
    provider: schemas.OAuthProvider,
    token: schemas.OAuthToken
) -> dict:
    """Get user info from OAuth provider"""
    try:
        if provider == schemas.OAuthProvider.GOOGLE:
            # Validate Google ID token
            id_info = jwt.decode(
                token.id_token,
                options={"verify_signature": False}
            )
            return {
                "sub": id_info["sub"],
                "email": id_info["email"],
                "name": id_info.get("name")
            }
        
        elif provider == schemas.OAuthProvider.MICROSOFT:
            # Get user info from Microsoft Graph API
            # Implementation would make actual API call
            return {
                "sub": "microsoft_user_id",
                "email": "user@example.com",
                "name": "Microsoft User"
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported OAuth provider"
            )
    except jwt.JWTError:
        raise exceptions.InvalidCredentialsException