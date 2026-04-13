from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import uuid

from app.db.session import get_db
from app.core.security import decode_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.models.user import User


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException("Missing or invalid authorization header")

    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise UnauthorizedException("Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Invalid token payload")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise UnauthorizedException("User not found or inactive")

    return user


async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise ForbiddenException("Admin access required")
    return current_user
