from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from db.database import Base, IST_TIMEZONE
from datetime import datetime

class JindalRegistrationModel(Base):
    __tablename__ = "jindal_registrations"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(15), nullable=False)
    jgu_student_id = Column(String(50), nullable=False, unique=True, index=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    selected_sports = Column(Text, nullable=True)  # JSON string of selected sports
    pickle_level = Column(String(50), nullable=True)  # For padel skill level
    total_amount = Column(Integer, nullable=False, default=0)
    payment_status = Column(String(50), nullable=False, default="pending")  # pending, completed, failed
    payment_proof = Column(String(500), nullable=True)  # File path/URL for payment proof
    agreed_to_terms = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), default=lambda: datetime.now(IST_TIMEZONE))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=lambda: datetime.now(IST_TIMEZONE), default=lambda: datetime.now(IST_TIMEZONE))

    def __repr__(self):
        return f"<JindalRegistrationModel(id={self.id}, name='{self.first_name} {self.last_name}', email='{self.email}', jgu_id='{self.jgu_student_id}')>"
