from enum import IntEnum


class ErrorCode(IntEnum):
    def __new__(cls, code, message, status_code, description):
        obj = int.__new__(cls, code)
        obj._value_ = code

        obj.code = code
        obj.message = message.upper()
        obj.status_code = status_code
        obj.description = description
        return obj

    def to_dict(self):
        return {
            "error_code": self.code,
            "message": self.message,
            "status_code": self.status_code,
            "description": self.description,
        }

    @classmethod
    def get_error_by_code(cls, code):
        for error in cls:
            if error.code == code:
                return error
        return cls.UNKNOWN_API_ERROR

    def __str__(self):
        return (
            f"Error Code: {self.code}, "
            f"Message: {self.message}, "
            f"HTTP Status Code: {self.status_code}, "
            f"Description: {self.description}"
        )

    # Authentication Errors (1000-1999)
    INVALID_CREDENTIALS = (1000, "Invalid credentials", 401, "Invalid credentials")
    USER_ALREADY_EXISTS = (1001, "User already exists", 400, "User already exists")
    TOKEN_EXPIRED = (1002, "Token expired", 401, "Authentication token has expired")
    INVALID_TOKEN = (1003, "Invalid token", 401, "Invalid authentication token")
    UNAUTHORIZED_ACCESS = (1004, "Unauthorized access", 403, "User does not have permission to access this resource")

    # Database Errors (4000-4999)
    DATABASE_ERROR = (4000, "Database error", 500, "An error occurred while accessing the database")
    RECORD_NOT_FOUND = (4001, "Record not found", 404, "The requested record was not found")
    DUPLICATE_RECORD = (4002, "Duplicate record", 400, "A record with this information already exists")

    # Server Errors (5000-5999)
    INTERNAL_SERVER_ERROR = (5000, "Internal server error", 500, "An unexpected error occurred")
    SERVICE_UNAVAILABLE = (5001, "Service unavailable", 503, "The service is temporarily unavailable")
    UNKNOWN_API_ERROR = (5002, "Unknown API error", 500, "An unknown error occurred")
    QUEUE_UNAVAILABLE = (5003, "Queue unavailable", 503, "The queue is temporarily unavailable")

    # API Errors (6000-6999)
    API_ERROR = (6000, "API error", 500, "An error occurred while accessing the API")
