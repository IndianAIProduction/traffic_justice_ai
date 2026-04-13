import uuid as _uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import UnauthorizedException, AppException
from app.schemas.auth import UserRegisterRequest, TokenResponse


async def register_user(data: UserRegisterRequest, db: AsyncSession) -> User:
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise AppException("Email already registered", status_code=409)

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        phone=data.phone,
        state=data.state,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def authenticate_user(email: str, password: str, db: AsyncSession) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise UnauthorizedException("Invalid email or password")

    if not user.is_active:
        raise UnauthorizedException("Account is deactivated")

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def refresh_tokens(refresh_token: str, db: AsyncSession) -> TokenResponse:
    payload = decode_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise UnauthorizedException("Invalid refresh token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == _uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise UnauthorizedException("User not found or inactive")

    new_access = create_access_token(data={"sub": str(user.id)})
    new_refresh = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)
