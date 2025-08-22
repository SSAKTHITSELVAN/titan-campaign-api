
### core/exceptions.py
from fastapi import HTTPException

class AuthError(HTTPException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=401, detail=detail)

class ValidationError(HTTPException):
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(status_code=400, detail=detail)

class EmailSendError(HTTPException):
    def __init__(self, detail: str = "Email sending failed"):
        super().__init__(status_code=500, detail=detail)

class PermissionError(HTTPException):
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status_code=403, detail=detail)
