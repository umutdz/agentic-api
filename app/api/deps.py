from typing import Optional

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import config
from app.core.error_codes import ErrorCode
from app.core.exceptions import ExceptionBase
from app.db.postgres.session import get_db
from app.schemas.auth import ActorSchema
from app.services.auth import AuthService
from app.services.jobs_orchestrator import JobsOrchestrator

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def depends_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


def depends_orchestrator() -> JobsOrchestrator:
    return JobsOrchestrator()


class ActorProvider:

    async def __call__(self, token: str = Depends(oauth2_scheme)):
        if not token:
            raise ExceptionBase(ErrorCode.UNAUTHORIZED_ACCESS)
        try:
            payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
            user_id: Optional[int] = payload.get("user_id")
            if user_id is None:
                raise ExceptionBase(ErrorCode.UNAUTHORIZED_ACCESS)
        except jwt.ExpiredSignatureError:
            raise ExceptionBase(ErrorCode.TOKEN_EXPIRED)
        except jwt.PyJWTError:
            raise ExceptionBase(ErrorCode.INVALID_TOKEN)

        actor = ActorSchema(user_id=user_id, is_active=payload.get("is_active"))
        return actor


require_authenticated_user = ActorProvider()
