from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from db.database import Base, IST_TIMEZONE
from datetime import datetime

class UserRegistrationModel(Base):
    __tablename__ = "user_registrations"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), index=True, nullable=False, unique=True)
    phone = Column(String(20), nullable=False)
    jgu_student_id = Column(String(50), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    agreed_to_terms = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), default=lambda: datetime.now(IST_TIMEZONE))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=lambda: datetime.now(IST_TIMEZONE), default=lambda: datetime.now(IST_TIMEZONE))
