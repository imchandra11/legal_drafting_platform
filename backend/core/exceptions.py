from fastapi import HTTPException, status
from typing import Optional, Dict, Any
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    """Standardized error response model"""
    error_code: str
    message: str
    detail: Optional[Dict[str, Any]] = None

class LegalPlatformException(HTTPException):
    """Base exception class for the platform"""
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        detail: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(
            status_code=status_code,
            detail=ErrorResponse(
                error_code=error_code,
                message=message,
                detail=detail
            ).dict(),
            headers=headers
        )
        self.error_code = error_code

# 400 Bad Request Errors
class InvalidTemplateException(LegalPlatformException):
    def __init__(self, template_id: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_TEMPLATE",
            message=f"Template {template_id} is invalid or malformed",
            detail={"template_id": template_id}
        )

class FieldValidationError(LegalPlatformException):
    def __init__(self, errors: Dict[str, str]):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="FIELD_VALIDATION",
            message="Document field validation failed",
            detail={"validation_errors": errors}
        )

# 401/403 Authentication Errors
class InvalidCredentialsException(LegalPlatformException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="INVALID_CREDENTIALS",
            message="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

class PermissionDeniedException(LegalPlatformException):
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="PERMISSION_DENIED",
            message=f"Access denied to {resource_type} {resource_id}",
            detail={
                "resource_type": resource_type,
                "resource_id": resource_id
            }
        )

# 404 Not Found Errors
class DocumentNotFoundException(LegalPlatformException):
    def __init__(self, document_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="DOCUMENT_NOT_FOUND",
            message=f"Document {document_id} not found",
            detail={"document_id": document_id}
        )

class TemplateNotFoundException(LegalPlatformException):
    def __init__(self, template_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="TEMPLATE_NOT_FOUND",
            message=f"Template {template_id} not found",
            detail={"template_id": template_id}
        )

# 409 Conflict Errors
class DraftFinalizedException(LegalPlatformException):
    def __init__(self, draft_id: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="DRAFT_FINALIZED",
            message=f"Draft {draft_id} is already finalized",
            detail={"draft_id": draft_id}
        )

# 422 Unprocessable Entity
class AIProcessingException(LegalPlatformException):
    def __init__(self, reason: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="AI_PROCESSING_ERROR",
            message="AI document processing failed",
            detail={"reason": reason}
        )

# 429 Rate Limiting
class RateLimitExceeded(LegalPlatformException):
    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            message="API rate limit exceeded",
            headers={"Retry-After": str(retry_after)}
        )

# 500 Server Errors
class StorageException(LegalPlatformException):
    def __init__(self, provider: str, operation: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="STORAGE_ERROR",
            message=f"{provider} storage operation failed",
            detail={
                "provider": provider,
                "operation": operation
            }
        )

class DatabaseException(LegalPlatformException):
    def __init__(self, operation: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            message="Database operation failed",
            detail={
                "operation": operation,
                "suggestion": "Check connection and retry"
            }
        )

# Exception handlers (to be registered in FastAPI app)
async def legal_platform_exception_handler(request, exc: LegalPlatformException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
        headers=exc.headers
    )

async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            detail=exc.errors()
        ).dict()
    )