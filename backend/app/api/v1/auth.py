from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import register_user, authenticate_user, refresh_tokens

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await register_user(data, db)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    return await authenticate_user(data.email, data.password, db)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    return await refresh_tokens(data.refresh_token, db)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
