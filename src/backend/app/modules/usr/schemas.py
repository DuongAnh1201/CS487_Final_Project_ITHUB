"""USR request and response models."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.usr.models import Role, UserStatus


class LoginRequest(BaseModel):
    """Credentials for POST /auth/login."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"email": "sa@sfbu.edu", "password": "AssistPass123"}]})

    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


class GoogleLoginRequest(BaseModel):
    """Google sign-in token: a Google Identity Services or Firebase ID token, per server setup."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6Ij..."}]})

    id_token: str = Field(min_length=1)


class FirebaseWebConfig(BaseModel):
    """Public Firebase web settings the login page initialises Firebase with."""

    api_key: str
    auth_domain: str
    project_id: str
    app_id: str | None


class AuthConfig(BaseModel):
    """What the frontend needs to decide whether, and how, to show the Google button."""

    google_enabled: bool
    google_provider: Literal["firebase", "google"] | None
    google_client_id: str | None
    firebase: FirebaseWebConfig | None


class ChangePasswordRequest(BaseModel):
    """Current and new password (US-USR-02)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"current_password": "TempPass123", "new_password": "NewPassword99"}]})

    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=1)


class ResetPasswordRequest(BaseModel):
    """Temporary password set by an Admin (US-USR-03)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"temporary_password": "ResetPass123"}]})

    temporary_password: str = Field(min_length=1)


class UserCreate(BaseModel):
    """New account (US-USR-04, FR-USR-03)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"full_name": "Sam Assistant", "email": "sa@sfbu.edu", "school_id": "SA-001", "role": "STUDENT_ASSISTANT", "access_end_date": "2026-12-18", "temporary_password": "TempPass123"}]})

    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    school_id: str = Field(min_length=1, max_length=50)
    role: Role
    access_end_date: date | None = None
    temporary_password: str = Field(min_length=1)


class UserUpdate(BaseModel):
    """Role and/or status change (US-USR-05, FR-USR-04)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"role": "ADMIN", "status": "ACTIVE"}]})

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


class StaffEntry(BaseModel):
    """One active account in the staff directory: just enough to pick a person."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    role: Role


class LoginResponse(BaseModel):
    """Result of a successful login."""

    access_token: str
    token_type: str = "bearer"
    must_change_password: bool
    user: UserRead


class MessageResponse(BaseModel):
    """Plain confirmation message."""

    message: str
