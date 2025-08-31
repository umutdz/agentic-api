from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.v1.router import api_router as api_router_v1
from app.core.config import config
from app.core.exceptions import ExceptionBase
from app.core.logging import default_logger
from app.middleware.rate_limit import init_limiter, rate_limit_middleware
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    default_logger.info("Application starting up...")
    await init_limiter()  # Initialize rate limiter

    try:
        yield
    finally:
        # Shutdown
        default_logger.info("Application shutting down...")
        # TODO: close the necessary connections


app = FastAPI(
    title=config.APP_NAME.format(name="Agentic AI"),
    version=config.APP_VERSION,
    openapi_url=f"{config.APP_STR}/openapi.json",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "docExpansion": "none",
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
    },
    lifespan=lifespan,
)

# middlewares
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.middleware("http")(rate_limit_middleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ORIGIN,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ExceptionBase)
def http_exception_handler(request, exc: ExceptionBase):
    default_logger.error(
        "API Error occurred",
        error_code=exc.code,
        error_message=exc.message,
        error_description=exc.description,
        status_code=exc.status_code,
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "description": exc.description,
        },
    )


# Include API router
app.include_router(api_router_v1, prefix=config.APP_STR)
app.include_router(health_router, prefix=config.APP_STR)
