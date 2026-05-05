from sqlalchemy import Column, String, DateTime, Enum, Boolean
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

