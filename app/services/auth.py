from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_codes import ErrorCode
from app.core.exceptions import ExceptionBase
from app.core.jwt import JWTManager
from app.core.security import get_password_hash, verify_password
from app.repositories.postgres.user import PostgresUserRepository
from app.schemas.auth import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenResponse,
    RegisterRequest,
    RegisterResponse,
    UserResponse,
)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.jwt_manager = JWTManager()

    async def register(self, request: RegisterRequest) -> RegisterResponse:
        is_user = await PostgresUserRepository(self.db).exists(email=request.email)
        if is_user:
            raise ExceptionBase(
                ErrorCode.USER_ALREADY_EXISTS,
            )

        user_data = request.model_dump()
        user_data["password"] = get_password_hash(user_data["password"])

        user = await PostgresUserRepository(self.db).create(user_data)
        return RegisterResponse(id=user.id, email=user.email, is_active=user.is_active)

    async def login(self, request: LoginRequest) -> LoginResponse:
        user = await PostgresUserRepository(self.db).filter_one(email=request.email)
        if not user:
            raise ExceptionBase(
                ErrorCode.INVALID_CREDENTIALS,
            )

        # Verify the password
        if not verify_password(request.password, user.password):
            raise ExceptionBase(
                ErrorCode.INVALID_CREDENTIALS,
            )

        # Create token data
        token_data = {"user_id": user.id, "email": user.email, "is_active": user.is_active}

        # Generate tokens using JWTManager
        access_token = self.jwt_manager.create_access_token(token_data)
        refresh_token = self.jwt_manager.create_refresh_token(token_data)

        return LoginResponse(access_token=access_token, refresh_token=refresh_token)

    async def get_user(self, token: str) -> UserResponse:
        try:
            payload = self.jwt_manager.verify_token(token)
            user_id = payload.get("user_id")
            user = await PostgresUserRepository(self.db).get(user_id)
            if not user:
                raise ExceptionBase(ErrorCode.INVALID_CREDENTIALS)
            return UserResponse(id=user.id, email=user.email, is_active=user.is_active)
        except Exception:
            raise ExceptionBase(ErrorCode.INVALID_CREDENTIALS)

    async def refresh_token(self, token: str) -> RefreshTokenResponse:
        try:
            payload = self.jwt_manager.verify_token(token)
            user_id = payload.get("user_id")
            user = await PostgresUserRepository(self.db).get(user_id)
            if not user:
                raise ExceptionBase(ErrorCode.INVALID_CREDENTIALS)

            token_data = {"user_id": user.id, "email": user.email, "is_active": user.is_active}

            access_token = self.jwt_manager.create_access_token(token_data)
            refresh_token = self.jwt_manager.create_refresh_token(token_data)

            return RefreshTokenResponse(access_token=access_token, refresh_token=refresh_token)
        except Exception:
            raise ExceptionBase(ErrorCode.INVALID_CREDENTIALS)

    async def change_password(self, token: str, request: ChangePasswordRequest) -> ChangePasswordResponse:
        try:
            # Verify token and get user
            payload = self.jwt_manager.verify_token(token)
            user_id = payload.get("user_id")
            user = await PostgresUserRepository(self.db).get(user_id)

            if not user:
                raise ExceptionBase(ErrorCode.INVALID_CREDENTIALS)

            # Verify old password
            if not verify_password(request.old_password, user.password):
                raise ExceptionBase(ErrorCode.INVALID_CREDENTIALS)

            # Hash and update new password
            hashed_password = get_password_hash(request.new_password)
            await PostgresUserRepository(self.db).update(user_id, {"password": hashed_password})

            return ChangePasswordResponse(success=True)

        except Exception:
            raise ExceptionBase(ErrorCode.INVALID_CREDENTIALS)
