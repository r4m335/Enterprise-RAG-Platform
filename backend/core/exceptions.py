from typing import Any
from fastapi import HTTPException

class AppException(Exception):
    def __init__(self, message: str, error_code: str, status_code: int = 400):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code

class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, "NOT_FOUND", 404)

class NotAuthorizedException(AppException):
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, "NOT_AUTHORIZED", 401)
        
class BadRequestException(AppException):
    def __init__(self, message: str = "Bad request"):
        super().__init__(message, "BAD_REQUEST", 400)
