"""Auth request/response schemas.

Kontrak login/rotasi token antara router auth dan client frontend.

Batas field pada schema menjaga input; aturan relasi dan otorisasi tetap
berada di service.
"""

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LoginRequest(BaseModel):
    """Masukan login dengan normalisasi whitespace semua field."""

    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    """Masukan refresh_token dengan alias kompatibilitas token."""

    refresh_token: Optional[str] = None
    token: Optional[str] = None

    @model_validator(mode="after")
    def _resolve(self):
        """Selaraskan alias token untuk kompatibilitas client.

        Returns:
            Objek RefreshRequest yang sama setelah refresh_token
            diselaraskan.

        Raises:
            ValueError: bila kedua input tidak menyediakan token.
        """
        if not self.refresh_token and self.token:
            self.refresh_token = self.token
        if not self.refresh_token:
            raise ValueError("refresh_token is required")
        return self


class TokenResponse(BaseModel):
    """Pasangan token akses dan refresh hasil login atau rotasi."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Identitas sesi tanpa hash password untuk endpoint auth/me."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool