import json
import logging
import os
import sys
import traceback
import uuid
from datetime import datetime, timezone
from functools import wraps
from logging.handlers import RotatingFileHandler
from typing import Optional

from app.core.config import config


class StructuredLogger:
    SENSITIVE_KEYS = {
        "authorization",
        "cookie",
        "set-cookie",
        "password",
        "passwd",
        "secret",
        "api_key",
        "x-api-key",
        "apikey",
        "token",
        "access_token",
        "refresh_token",
        "id_token",
        "jwt",
        "session",
    }

    def __init__(
        self, name: str, log_level: str = "INFO", log_file: Optional[str] = None, max_bytes: int = 10485760, backup_count: int = 5  # 10MB
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))

        # Create formatters
        json_formatter = logging.Formatter("%(message)s")

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(json_formatter)
        self.logger.addHandler(console_handler)

        # File handler if log_file is specified
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
            file_handler.setFormatter(json_formatter)
            self.logger.addHandler(file_handler)

    def _format_log(self, level: str, message: str, **kwargs) -> str:
        # Filter sensitive data
        if "headers" in kwargs and isinstance(kwargs["headers"], dict):
            for key, value in kwargs["headers"].items():
                if key.lower() in self.SENSITIVE_KEYS:
                    kwargs["headers"][key] = "********"
                else:
                    kwargs["headers"][key] = value

        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            "service": self.logger.name,
            **kwargs,
        }
        return json.dumps(log_data)

    def debug(self, message: str, **kwargs):
        self.logger.debug(self._format_log("DEBUG", message, **kwargs))

    def info(self, message: str, **kwargs):
        self.logger.info(self._format_log("INFO", message, **kwargs))

    def warning(self, message: str, **kwargs):
        self.logger.warning(self._format_log("WARNING", message, **kwargs))

    def error(self, message: str, **kwargs):
        self.logger.error(self._format_log("ERROR", message, **kwargs))

    def critical(self, message: str, **kwargs):
        self.logger.critical(self._format_log("CRITICAL", message, **kwargs))


def log_execution(logger: StructuredLogger):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request_id = str(uuid.uuid4())
            start_time = datetime.now(timezone.utc)

            try:
                logger.info(
                    f"Starting execution of {func.__name__}",
                    request_id=request_id,
                    function=func.__name__,
                    args=str(args),
                    kwargs=str(kwargs),
                )

                result = await func(*args, **kwargs)

                execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
                logger.info(
                    f"Completed execution of {func.__name__}", request_id=request_id, function=func.__name__, execution_time=execution_time
                )

                return result

            except Exception as e:
                execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
                logger.error(
                    f"Error in {func.__name__}",
                    request_id=request_id,
                    function=func.__name__,
                    error=str(e),
                    traceback=traceback.format_exc(),
                    execution_time=execution_time,
                )
                raise

        return wrapper

    return decorator


# Create default logger instance
default_logger = StructuredLogger(name="app", log_level=config.LOG_LEVEL, log_file=config.LOG_FILE)
