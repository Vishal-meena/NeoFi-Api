from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from models import Role, RecurrencePattern

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Event schemas
class EventBase(BaseModel):
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[RecurrencePattern] = None
    recurrence_end_date: Optional[datetime] = None

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[RecurrencePattern] = None
    recurrence_end_date: Optional[datetime] = None

class Event(EventBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class EventWithPermissions(Event):
    permissions: List[Dict[str, Any]]
    
    class Config:
        orm_mode = True

# Permission schemas
class PermissionCreate(BaseModel):
    user_id: int
    role: Role

class PermissionUpdate(BaseModel):
    role: Role

class Permission(BaseModel):
    user_id: int
    role: Role
    created_at: datetime
    
    class Config:
        orm_mode = True

# Version schemas
class EventVersion(BaseModel):
    id: int
    event_id: int
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    is_recurring: bool
    recurrence_pattern: Optional[RecurrencePattern] = None
    recurrence_end_date: Optional[datetime] = None
    modified_by_id: int
    version_number: int
    created_at: datetime
    
    class Config:
        orm_mode = True

# Diff schemas
class DiffItem(BaseModel):
    field: str
    old_value: Any
    new_value: Any

class VersionDiff(BaseModel):
    version1: int
    version2: int
    differences: List[DiffItem]

# Batch operation schemas
class BatchEventCreate(BaseModel):
    events: List[EventCreate]