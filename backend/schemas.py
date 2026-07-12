from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field


PriorityType = Literal["urgent", "normal", "low"]


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserRead(BaseModel):
    id: str
    username: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    priority: PriorityType = "normal"
    deadline: Optional[datetime] = None
    photo_url: Optional[str] = None
    ai_extracted: bool = False


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    text: Optional[str] = Field(None, min_length=1, max_length=5000)
    priority: Optional[PriorityType] = None
    deadline: Optional[datetime] = None
    photo_url: Optional[str] = None
    ai_extracted: Optional[bool] = None


class TaskRead(TaskBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
