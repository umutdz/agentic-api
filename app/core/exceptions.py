from app.core.error_codes import ErrorCode


class ExceptionBase(Exception):
    def __init__(self, error: ErrorCode, description: str = None):
        self.code = error.code
        self.message = error.message
        self.status_code = error.status_code
        self.description = description or error.description


class RequestTimeoutException(ExceptionBase):
    pass


class NotFoundException(ExceptionBase):
    pass


class QueueUnavailable(ExceptionBase):
    pass
