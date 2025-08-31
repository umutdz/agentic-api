import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

# from app.db.mongodb.mongodb import MongoDB
from app.db.postgres.session import check_db_connection, get_db

router = APIRouter(prefix="/health", tags=["health"], include_in_schema=False)
logger = logging.getLogger(__name__)


@router.get("")
def health(request: Request):
    """
    Root health check endpoint.
    Returns basic application info and status.
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "request_id": request.state.request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@router.get("/db")
async def db_health(db: AsyncSession = Depends(get_db)):
    """
    Database health check.
    Verifies connection to the database.
    """
    try:
        is_connected = await check_db_connection(db)
        return {
            "status": "ok" if is_connected else "error",
            "database": "connected" if is_connected else "disconnected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ready")
def readiness():
    """
    # TODO: add readiness probe for Kubernetes
    """
    return {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# @router.get("/mongodb")
# async def mongodb_health():
#     """
#     MongoDB health check.
#     Verifies connection to MongoDB.
#     """
#     try:
#         client = await MongoDB.connect()
#         # Test the connection
#         await client.admin.command("ping")
#         return {
#             "status": "ok",
#             "mongodb": "connected",
#             "timestamp": datetime.now(timezone.utc).isoformat(),
#         }
#     except Exception as e:
#         logger.error(f"MongoDB health check failed: {str(e)}")
#         return {
#             "status": "error",
#             "mongodb": "disconnected",
#             "error": str(e),
#             "timestamp": datetime.now(timezone.utc).isoformat(),
#         }
