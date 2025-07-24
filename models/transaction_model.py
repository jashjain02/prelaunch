from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from db.database import Base

class TransactionModel(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    event_registration_id = Column(Integer, ForeignKey("event_registrations.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False)  # e.g., 'pending', 'success', 'failed'
    razorpay_payment_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 