"""Auth request/response schemas."""

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: Optional[str] = None
    token: Optional[str] = None

    @model_validator(mode="after")
    def _resolve(self):
        if not self.refresh_token and self.token:
            self.refresh_token = self.token
        if not self.refresh_token:
            raise ValueError("refresh_token is required")
        return self


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool