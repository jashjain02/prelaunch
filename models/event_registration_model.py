from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from db.database import Base

class EventRegistrationModel(Base):
    __tablename__ = "event_registrations"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, index=True, nullable=False)
    phone = Column(String, nullable=False)
    selected_sports = Column(Text, nullable=False)  # JSON stringified list
    pickleball_level = Column(String, nullable=True)
    file_url = Column(String, nullable=True)
    booking_id = Column(String(8), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 
    