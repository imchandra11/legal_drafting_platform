import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):



    PROJECT_NAME: str = "LegalDraft"
    DATABASE_URL: str = os.getenv("DB_URL", "postgresql+asyncpg://user:pass@db:5432/legaldraft")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "supersecret")
    JWT_ALGORITHM: str = "HS256"
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID")
    ONEDRIVE_CLIENT_ID: str = os.getenv("ONEDRIVE_CLIENT_ID")
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 15
    OAUTH_REDIRECT_URI: str = "http://localhost:3000/oauth/callback"
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    MICROSOFT_CLIENT_ID: str = os.getenv("MICROSOFT_CLIENT_ID", "")
    MICROSOFT_CLIENT_SECRET: str = os.getenv("MICROSOFT_CLIENT_SECRET", "")
    class Config:
        case_sensitive = True

settings = Settings()