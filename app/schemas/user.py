"""
Schemas for user-related data models.
"""

from pydantic import BaseModel

# This is the inputs needed for registeing a user 
class UserCreate(BaseModel):
    """Schema for creating a user."""
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str

class UserLoginSuccess(BaseModel):
    id: str
    username: str
    email: str
    access_token: str
    token_type: str


class User(BaseModel):
    """Schema for returning user data"""
    id: str
    username: str
    email: str
    is_admin: bool

    model_config = {"from_attributes": True}

__all__ = ["UserCreate", "User"]