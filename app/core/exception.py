"""
exceptions.py
Custom Exception Handling for Email Campaign Application
"""

# Base Exception
class CampaignCoreException(Exception):
    """Base exception for all Campaign-related errors."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# Auth & Security Errors
class AuthException(CampaignCoreException):
    """Authentication or Authorization failed."""
    def __init__(self, message="Authentication failed", status_code=401):
        super().__init__(message, status_code)


class PermissionDeniedException(CampaignCoreException):
    """User doesn't have permission."""
    def __init__(self, message="Permission denied", status_code=403):
        super().__init__(message, status_code)


# Database & Data Errors
class DataBaseException(CampaignCoreException):
    """Database-related errors."""
    def __init__(self, message="Database error", status_code=500):
        super().__init__(message, status_code)


class DataNotFoundException(CampaignCoreException):
    """Requested data not found."""
    def __init__(self, message="Data not found", status_code=404):
        super().__init__(message, status_code)


class DataValidationException(CampaignCoreException):
    """Invalid data format or constraints."""
    def __init__(self, message="Invalid data", status_code=422):
        super().__init__(message, status_code)


# Email Sending Errors
class EmailSendException(CampaignCoreException):
    """Failed to send email."""
    def __init__(self, message="Email sending failed", status_code=502):
        super().__init__(message, status_code)


# External API Errors
class ExternalAPIException(CampaignCoreException):
    """Error communicating with an external API."""
    def __init__(self, message="External API error", status_code=502):
        super().__init__(message, status_code)


# File Handling Errors (e.g., template uploads)
class FileHandlingException(CampaignCoreException):
    """Error processing file."""
    def __init__(self, message="File processing error", status_code=500):
        super().__init__(message, status_code)


# Rate Limit & Throttling
class RateLimitException(CampaignCoreException):
    """Too many requests in a short time."""
    def __init__(self, message="Rate limit exceeded", status_code=429):
        super().__init__(message, status_code)
