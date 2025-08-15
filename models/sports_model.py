from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from db.database import Base, IST_TIMEZONE
from datetime import datetime

class SportsModel(Base):
    __tablename__ = "sports"

    id = Column(Integer, primary_key=True, index=True)
    sport_name = Column(String(100), nullable=False, unique=True)
    sport_key = Column(String(50), nullable=False, unique=True)  # e.g., "padel", "strength", "breathwork"
    description = Column(Text, nullable=True)
    price = Column(Integer, nullable=False, default=0)  # Price in INR
    max_capacity = Column(Integer, nullable=False, default=50)  # Maximum tickets available
    current_count = Column(Integer, nullable=False, default=0)  # Current tickets sold
    is_active = Column(Boolean, default=True, nullable=False)  # Whether sport is available for booking
    is_sold_out = Column(Boolean, default=False, nullable=False)  # Sold out status
    timing = Column(String(100), nullable=True)  # e.g., "4-8pm"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), default=lambda: datetime.now(IST_TIMEZONE))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=lambda: datetime.now(IST_TIMEZONE), default=lambda: datetime.now(IST_TIMEZONE))

    def __repr__(self):
        return f"<SportsModel(sport_name='{self.sport_name}', current_count={self.current_count}/{self.max_capacity}, sold_out={self.is_sold_out})>"

    @property
    def remaining_tickets(self) -> int:
        """Calculate remaining tickets"""
        return max(0, self.max_capacity - self.current_count)

    @property
    def is_available(self) -> bool:
        """Check if sport is available for booking"""
        return self.is_active and not self.is_sold_out and self.current_count < self.max_capacity

    def increment_count(self, count: int = 1) -> bool:
        """
        Increment ticket count and check if sold out
        Returns True if successful, False if would exceed capacity
        """
        if self.current_count + count > self.max_capacity:
            return False
        
        self.current_count += count
        
        # Check if sold out after increment
        if self.current_count >= self.max_capacity:
            self.is_sold_out = True
            self.is_active = False
        
        return True

    def decrement_count(self, count: int = 1) -> bool:
        """
        Decrement ticket count and update sold out status
        Returns True if successful, False if would go below 0
        """
        if self.current_count - count < 0:
            return False
        
        self.current_count -= count
        
        # If count decreased and was previously sold out, make available again
        if self.is_sold_out and self.current_count < self.max_capacity:
            self.is_sold_out = False
            self.is_active = True
        
        return True

    def reset_count(self) -> None:
        """Reset count to 0 and make available"""
        self.current_count = 0
        self.is_sold_out = False
        self.is_active = True

    def set_capacity(self, new_capacity: int) -> None:
        """Set new capacity and update availability"""
        self.max_capacity = new_capacity
        
        # Update sold out status based on new capacity
        if self.current_count >= new_capacity:
            self.is_sold_out = True
            self.is_active = False
        else:
            self.is_sold_out = False
            self.is_active = True
