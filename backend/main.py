import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core import config, database, exceptions
from backend.core.exceptions import (
    LegalPlatformException,
    validation_exception_handler,
    ErrorResponse
)
from backend.apps.auth import routers as auth_routers
from backend.apps.documents import routers as document_routers
from backend.apps.templates import routers as template_routers
from backend.apps.signatures import routers as signature_routers
from backend.utils import gdpr_utils
from backend.storage import base_provider






# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# OAuth2 scheme for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management with startup/shutdown events"""
    # Initialize database connection
    await database.engine.connect()
    logger.info("Database connection established")
    
    # Initialize cloud storage providers
    base_provider.StorageProviderFactory.initialize_providers()
    logger.info("Storage providers initialized")
    
    yield  # App runs here
    
    # Cleanup on shutdown
    await database.engine.dispose()
    logger.info("Database connection closed")

# Create FastAPI application
app = FastAPI(
    title=config.settings.PROJECT_NAME,
    description="Legal Document Drafting & E-Signature Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(LegalPlatformException, exceptions.legal_platform_exception_handler)
app.add_exception_handler(HTTPException, exceptions.http_exception_handler)
app.add_exception_handler(Exception, exceptions.generic_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Register routers
app.include_router(
    auth_routers.router,
    prefix="/api/auth",
    tags=["Authentication"]
)

app.include_router(
    template_routers.router,
    prefix="/api/templates",
    tags=["Templates"],
    dependencies=[Depends(oauth2_scheme)]
)

app.include_router(
    document_routers.router,
    prefix="/api/documents",
    tags=["Documents"],
    dependencies=[Depends(oauth2_scheme)]
)

app.include_router(
    signature_routers.router,
    prefix="/api/signatures",
    tags=["Signatures"],
    dependencies=[Depends(oauth2_scheme)]
)

# GDPR compliance endpoint
@app.post(
    "/api/gdpr/redact-user",
    tags=["Compliance"],
    response_model=ErrorResponse,
    status_code=status.HTTP_200_OK
)
async def gdpr_redact_user(
    user_id: str,
    db: AsyncSession = Depends(database.get_db)
):
    """GDPR-compliant user data redaction endpoint"""
    try:
        await gdpr_utils.anonymize_user_data(user_id, db)
        return JSONResponse(
            content={
                "message": f"User {user_id} data redacted successfully"
            }
        )
    except Exception as e:
        logger.error(f"GDPR redaction failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "GDPR_REDACTION_FAILED",
                "message": f"Failed to redact user data: {str(e)}"
            }
        )

# Health check endpoint
@app.get("/api/health", tags=["System"])
async def health_check():
    """System health check endpoint"""
    return {
        "status": "OK",
        "version": app.version,
        "database": "connected" if database.engine else "disconnected"
    }

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    # Add security headers for SOC2 compliance
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "same-origin"
    return response

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        raise
    logger.info(f"Response status: {response.status_code}")
    return response

# Main entry point for development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        ssl_keyfile=config.settings.SSL_KEY_PATH,
        ssl_certfile=config.settings.SSL_CERT_PATH
    )