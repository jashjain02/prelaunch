from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from db.database import Base

class OrangetheoryRegistrationModel(Base):
    __tablename__ = "orangetheory_registrations"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, index=True, nullable=False)
    phone = Column(String, nullable=False)
    selected_sports = Column(Text, nullable=False)  # JSON stringified list
    orangetheory_batch = Column(String, nullable=True)  # "batch1" or "batch2"
    event_date = Column(String, nullable=True)  # "24th August 2025"
    event_location = Column(String, nullable=True)  # "Orangetheory Fitness, Worli"
    payment_status = Column(String, default="pending")  # "pending", "completed", "failed"
    file_url = Column(String, nullable=True)
    booking_id = Column(String(8), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)  # For soft deletes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
