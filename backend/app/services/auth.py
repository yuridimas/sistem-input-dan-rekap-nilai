"""Authentication service: password hashing, JWT, user lookup.

Primitif autentikasi untuk router auth, dependency pengguna, dan service
users.

Hash password dan token terpusat agar semua jalur memakai kebijakan yang
sama.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import User

settings = get_settings()

ALGORITHM = settings.jwt_algorithm
SECRET_KEY = settings.jwt_secret

# In-memory set of revoked refresh-token jti (rotation).
# WARNING: Daftar ini hilang saat restart dan tidak dibagikan ke proses/worker lain.
_REVOKED_REFRESH_JTI: set[str] = set()


def verify_password(plain: str, hashed: str) -> bool:
    """Bandingkan password dan hash tanpa membocorkan error bcrypt.

    Args:
        plain: Password plaintext yang akan di-hash atau diverifikasi.
        hashed: Hash bcrypt tersimpan yang dibandingkan dengan
            plaintext.

    Returns:
        False untuk password salah atau input/hash ditolak bcrypt.
    """
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def hash_password(plain: str, rounds: int = 12) -> str:
    """Buat hash bersalt; rounds mengatur biaya bcrypt, default 12.

    Error bcrypt diteruskan untuk input yang tidak didukung.

    Args:
        plain: Password plaintext yang akan di-hash atau diverifikasi.
        rounds: Biaya bcrypt; default 12.
    """
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=rounds)).decode("utf-8")


def _now() -> datetime:
    """Gunakan waktu UTC berzona untuk timestamp token."""
    return datetime.now(timezone.utc)


def create_access_token(subject: str, role: str, expires_delta: timedelta | None = None) -> str:
    """Terbitkan JWT akses dengan identitas dan role akun.

    Tidak menulis DB.

    Args:
        subject: Identitas akun yang disimpan pada klaim sub JWT.
        role: Role akun atau filter role yang dipakai operasi.
        expires_delta: Durasi token opsional; None memakai konfigurasi
            masa berlaku.

    Returns:
        JWT akses bertanda tangan untuk identitas dan role akun.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expire = _now() + expires_delta
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": str(role),
        "type": "access",
        "iat": int(_now().timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(subject: str, role: str, expires_delta: timedelta | None = None) -> str:
    """Terbitkan JWT refresh terpisah untuk rotasi sesi.

    Tidak menulis DB.

    Args:
        subject: Identitas akun yang disimpan pada klaim sub JWT.
        role: Role akun atau filter role yang dipakai operasi.
        expires_delta: Durasi token opsional; None memakai konfigurasi
            masa berlaku.

    Returns:
        JWT refresh bertanda tangan dengan jti baru untuk rotasi.
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.refresh_token_expire_days)
    expire = _now() + expires_delta
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": str(role),
        "type": "refresh",
        "iat": int(_now().timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Verifikasi signature dan klaim JWT dengan algoritma konfigurasi.

    Pemanggil tetap harus memeriksa klaim type sesuai jenis operasi.

    Args:
        token: JWT yang diverifikasi sebelum identitasnya dipercaya.

    Returns:
        Dict klaim JWT yang sudah lolos verifikasi signature dan waktu
        berlaku.

    Raises:
        JWTError: Raises JWTError untuk token invalid/kedaluwarsa.
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


async def get_user_by_id(db: AsyncSession, user_id: str | uuid.UUID) -> User | None:
    """Cari identitas token; UUID invalid diperlakukan sebagai absen.

    Hanya membaca DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        user_id: Identitas akun yang dicari atau dikelola.

    Returns:
        None jika UUID invalid atau akun absen.
    """
    try:
        uid = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
    except (ValueError, TypeError):
        return None
    result = await db.execute(select(User).where(User.id == uid))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """Terima login hanya untuk akun aktif dengan password cocok.

    Hanya membaca DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        email: Email akun yang dipakai untuk pencarian identitas.
        password: Password plaintext yang diverifikasi terhadap hash
            akun.

    Returns:
        None jika akun absen/nonaktif atau password salah.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def revoke_refresh_jti(jti: str) -> None:
    """Catat jti terpakai untuk menolak penggunaan ulang token refresh.

    Mengubah set global proses; tidak persisten antar-worker.

    Args:
        jti: Identitas unik token refresh yang diperiksa atau dicabut.
    """
    _REVOKED_REFRESH_JTI.add(jti)


def is_refresh_revoked(jti: str) -> bool:
    """Periksa jti pada daftar pencabutan di proses ini.

    Args:
        jti: Identitas unik token refresh yang diperiksa atau dicabut.
    """
    return jti in _REVOKED_REFRESH_JTI


# slowapi limiter (shared)
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)