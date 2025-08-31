import logging

import aioredis
from fastapi import Request, Response
from fastapi_limiter import FastAPILimiter

from app.core.config import config

logger = logging.getLogger(__name__)


async def init_limiter():
    """
    Initialize the rate limiter
    """
    try:
        redis_client = await aioredis.from_url(
            config.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

        # Test Redis connection
        await redis_client.set("test", "test")
        logger.info("Redis connection successful")

        # Initialize FastAPILimiter
        FastAPILimiter.init(redis_client)
        logger.info("Rate limiter initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize rate limiter: {str(e)}")
        raise


async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limit middleware
    """
    try:
        # Get the rate limiter for the current endpoint
        limiter = getattr(request.app.state, "rate_limiter", None)
        if limiter:
            await limiter(request)

        # Process the request
        response = await call_next(request)
        return response
    except Exception as e:
        # Handle rate limit exceeded
        if "rate limit exceeded" in str(e).lower():
            return Response(
                content="Rate limit exceeded",
                status_code=429,
                headers={
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": "0",
                },
            )
        raise e
