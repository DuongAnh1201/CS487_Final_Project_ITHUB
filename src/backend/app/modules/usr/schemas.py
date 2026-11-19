"""USR request and response models."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.usr.models import Role, UserStatus


class LoginRequest(BaseModel):
    """Credentials for POST /auth/login."""

    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


class GoogleLoginRequest(BaseModel):
    """Google ID token from Google Identity Services."""

    id_token: str = Field(min_length=1)


class AuthConfig(BaseModel):
    """What the frontend needs to decide whether to show the Google button."""

    google_enabled: bool
    google_client_id: str | None


class ChangePasswordRequest(BaseModel):
    """Current and new password (US-USR-02)."""

    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=1)


class ResetPasswordRequest(BaseModel):
    """Temporary password set by an Admin (US-USR-03)."""

    temporary_password: str = Field(min_length=1)


class UserCreate(BaseModel):
    """New account (US-USR-04, FR-USR-03)."""

    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    school_id: str = Field(min_length=1, max_length=50)
    role: Role
    access_end_date: date | None = None
    temporary_password: str = Field(min_length=1)


class UserUpdate(BaseModel):
    """Role and/or status change (US-USR-05, FR-USR-04)."""

    role: Role | None = None
    status: UserStatus | None = None


class UserRead(BaseModel):
    """Public view of a user; never includes the password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    school_id: str
    role: Role
    status: UserStatus
    must_change_password: bool
    access_end_date: date | None
    last_login_at: datetime | None
    created_at: datetime


class LoginResponse(BaseModel):
    """Result of a successful login."""

    access_token: str
    token_type: str = "bearer"
    must_change_password: bool
    user: UserRead


class MessageResponse(BaseModel):
    """Plain confirmation message."""

    message: str
