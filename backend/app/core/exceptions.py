"""
Custom Exceptions
"""
from fastapi import HTTPException, status

class APIException(HTTPException):
    def __init__(self, status_code: int = 500, detail: str = "Internal server error", error_code: str = "INTERNAL_ERROR"):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code

class AuthenticationException(APIException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, error_code="AUTH_FAILED")

class NotFoundException(APIException):
    def __init__(self, detail: str = "Not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail, error_code="NOT_FOUND")

class ValidationException(APIException):
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail, error_code="VALIDATION_ERROR")

class ExternalServiceException(APIException):
    def __init__(self, detail: str = "External service error", service: str = "unknown"):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail, error_code=f"EXTERNAL_ERROR_{service.upper()}")
