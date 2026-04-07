from sqlalchemy import Column, String, DateTime
from database import Base
import datetime

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String, primary_key=True, index=True)
    firstname = Column(String, nullable=True)
    lastname = Column(String, nullable=True)
    account_type = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
