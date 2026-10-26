"""Auth router: login, refresh, me.

Adapter HTTP login dan rotasi sesi yang didaftarkan app.main.

Dependency menetapkan identitas/role; aturan bisnis dan persistence
didelegasikan ke service.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import TokenResponse, UserResponse
from app.services.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_by_id,
    is_refresh_revoked,
    limiter,
    revoke_refresh_jti,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _norm_role(role: Any) -> str:
    """Samakan nilai enum/string untuk role dalam JWT.

    Args:
        role: Role akun atau filter role yang dipakai operasi.
    """
    return str(role.value) if hasattr(role, "value") else str(role)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("30/minute")
async def login(request: Request, db: AsyncSession = Depends(get_db)):
    """Terbitkan pasangan token setelah login JSON atau form.

    \f

    Args:
        request: Request HTTP untuk membaca input, header, atau konteks
            limiter.
        db: Session database; batas commit mengikuti operasi terkait.

    Returns:
        Pasangan token akses dan refresh yang baru.

    Raises:
        HTTPException: 422 jika kredensial absen, 401 jika login
            ditolak.
        RateLimitExceeded: Percobaan melebihi batas limiter.
    """
    # Support JSON and form-encoded bodies.
    email: str | None = None
    password: str | None = None
    content_type = request.headers.get("content-type", "")
    try:
        if "application/json" in content_type:
            body = await request.json()
            if isinstance(body, dict):
                email = body.get("email") or body.get("username")
                password = body.get("password")
        else:
            form = await request.form()
            email = form.get("email") or form.get("username")
            password = form.get("password")
    except Exception:
        pass

    if not email or not password:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Missing credentials")

    user = await authenticate_user(db, str(email), str(password))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return TokenResponse(
        access_token=create_access_token(str(user.id), _norm_role(user.role)),
        refresh_token=create_refresh_token(str(user.id), _norm_role(user.role)),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, db: AsyncSession = Depends(get_db)):
    """Rotasi token refresh yang masih valid untuk akun aktif.

    \f

    Mutasi daftar revoked proses.

    Args:
        request: Request HTTP untuk membaca input, header, atau konteks
            limiter.
        db: Session database; batas commit mengikuti operasi terkait.

    Returns:
        Pasangan token akses dan refresh pengganti.

    Raises:
        HTTPException: 422 token absen, 401 invalid.
    """
    token: str | None = None
    # query param
    token = request.query_params.get("refresh_token") or request.query_params.get("token")
    content_type = request.headers.get("content-type", "")
    if not token:
        try:
            if "application/json" in content_type:
                body = await request.json()
                if isinstance(body, dict):
                    token = body.get("refresh_token") or body.get("token")
            else:
                form = await request.form()
                token = form.get("refresh_token") or form.get("token")
        except Exception:
            pass
    # body as raw string
    # Urutan kompatibilitas: query, JSON/form, lalu raw body; sumber awal yang ada menang.
    if not token:
        try:
            raw = (await request.body()).decode("utf-8").strip()
            if raw and not raw.startswith("{"):
                token = raw.strip('"')
        except Exception:
            pass

    if not token:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="refresh_token is required")

    try:
        payload = decode_token(str(token))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    jti = payload.get("jti")
    if jti and is_refresh_revoked(str(jti)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")

    user = await get_user_by_id(db, payload.get("sub"))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    if jti:
        revoke_refresh_jti(str(jti))

    role = _norm_role(user.role)
    return TokenResponse(
        access_token=create_access_token(str(user.id), role),
        refresh_token=create_refresh_token(str(user.id), role),
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """Sajikan identitas sesi aktif tanpa hash password.

    \f

    Args:
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Returns:
        Identitas akun aktif, diserialisasi tanpa hash password.
    """
    return current_user