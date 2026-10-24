"""FastAPI dependencies shared across routers."""

from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.services.auth import decode_token, get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

__all__ = ["get_settings", "get_db", "get_current_user", "require_role", "oauth2_scheme"]


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str | None = Depends(oauth2_scheme),
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_type = payload.get("type")
    if token_type not in (None, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await get_user_by_id(db, payload.get("sub"))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def _normalize_role(value: Any) -> str:
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def require_role(*roles: Any):
    normalized: list[str] = []
    for role in roles:
        if isinstance(role, (list, tuple, set)):
            for item in role:
                normalized.append(_normalize_role(item))
        else:
            normalized.append(_normalize_role(role))

    async def _dependency(user: User = Depends(get_current_user)) -> User:
        if str(getattr(user, "role", "")) not in normalized:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _dependency