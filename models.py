from sqlalchemy import Column, String, DateTime, Enum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import datetime
import enum

class AccountType(str, enum.Enum):
    STUDENT = "student"
    ADMIN = "admin"

class Users(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    firstname = Column(String)
    lastname = Column(String)
    account_type = Column(String, default="student", nullable=False)
    avatar_url = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)
    is_online = Column(Boolean, default=False)
    last_active = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Tasks(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="Pending") # Pending, In Progress, Completed
    assigned_to = Column(String, ForeignKey("users.id"), nullable=True)
    location = Column(String, nullable=True)
    hours = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    assignee = relationship("Users", foreign_keys=[assigned_to])

