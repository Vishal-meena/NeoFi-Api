from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Table, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

# Role-based access control
class Role(str, enum.Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"

# Association table for event permissions
event_permissions = Table(
    "event_permissions",
    Base.metadata,
    Column("event_id", Integer, ForeignKey("events.id")),
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("role", Enum(Role), default=Role.VIEWER),
    Column("created_at", DateTime, default=datetime.utcnow),
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owned_events = relationship("Event", back_populates="owner")
    shared_events = relationship("Event", secondary=event_permissions, back_populates="shared_users")

class RecurrencePattern(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    location = Column(String, nullable=True)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(Enum(RecurrencePattern), nullable=True)
    recurrence_end_date = Column(DateTime, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="owned_events")
    shared_users = relationship("User", secondary=event_permissions, back_populates="shared_events")
    versions = relationship("EventVersion", back_populates="event")

class EventVersion(Base):
    __tablename__ = "event_versions"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    title = Column(String)
    description = Column(Text)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    location = Column(String, nullable=True)
    is_recurring = Column(Boolean)
    recurrence_pattern = Column(Enum(RecurrencePattern), nullable=True)
    recurrence_end_date = Column(DateTime, nullable=True)
    modified_by_id = Column(Integer, ForeignKey("users.id"))
    version_number = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    event = relationship("Event", back_populates="versions")
    modified_by = relationship("User")