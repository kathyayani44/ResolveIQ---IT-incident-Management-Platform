from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class UserLogin(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserRegister(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=4, description="User password")
    name: Optional[str] = Field(default=None, description="Display name")


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    token: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class JiraConnectionResponse(BaseModel):
    connected: bool
    domain: Optional[str] = None
    displayName: Optional[str] = None
    emailAddress: Optional[str] = None
    error: Optional[str] = None
