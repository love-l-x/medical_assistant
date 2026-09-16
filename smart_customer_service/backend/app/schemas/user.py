from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    username: str

    email:EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str

    token_type: str

    user_id: int

class TokenData(BaseModel):
    user_id : Optional[int] = None