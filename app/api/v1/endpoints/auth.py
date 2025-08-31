from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

from app.api.deps import depends_auth_service
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
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

auth2 = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/register")
async def register(request: RegisterRequest, service: AuthService = Depends(depends_auth_service)) -> RegisterResponse:
    return await service.register(request)


@router.post("/login")
async def login(request: LoginRequest, service: AuthService = Depends(depends_auth_service)) -> LoginResponse:
    return await service.login(request)


@router.get("/me")
async def get_user(token: str = Depends(auth2), service: AuthService = Depends(depends_auth_service)) -> UserResponse:
    return await service.get_user(token)


@router.post("/refresh-token")
async def refresh_token(token: str = Depends(auth2), service: AuthService = Depends(depends_auth_service)) -> RefreshTokenResponse:
    return await service.refresh_token(token)


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest, token: str = Depends(auth2), service: AuthService = Depends(depends_auth_service)
) -> ChangePasswordResponse:
    return await service.change_password(token, request)
