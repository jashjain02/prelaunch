from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime

class SportsBase(BaseModel):
    sport_name: str
    sport_key: str
    description: Optional[str] = None
    price: int
    max_capacity: int
    timing: Optional[str] = None
    is_active: bool = True

    @validator('sport_name')
    def validate_sport_name(cls, v):
        if not v.strip():
            raise ValueError('Sport name cannot be empty')
        return v.strip()

    @validator('sport_key')
    def validate_sport_key(cls, v):
        if not v.strip():
            raise ValueError('Sport key cannot be empty')
        return v.strip().lower()

    @validator('price')
    def validate_price(cls, v):
        if v < 0:
            raise ValueError('Price cannot be negative')
        return v

    @validator('max_capacity')
    def validate_max_capacity(cls, v):
        if v <= 0:
            raise ValueError('Max capacity must be greater than 0')
        return v

class SportsCreate(SportsBase):
    pass

class SportsUpdate(BaseModel):
    sport_name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    max_capacity: Optional[int] = None
    timing: Optional[str] = None
    is_active: Optional[bool] = None

    @validator('price')
    def validate_price(cls, v):
        if v is not None and v < 0:
            raise ValueError('Price cannot be negative')
        return v

    @validator('max_capacity')
    def validate_max_capacity(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Max capacity must be greater than 0')
        return v

class SportsResponse(SportsBase):
    id: int
    current_count: int
    is_sold_out: bool
    remaining_tickets: int
    is_available: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SportsAvailabilityResponse(BaseModel):
    sport_key: str
    sport_name: str
    description: Optional[str] = None
    price: int
    current_count: int
    max_capacity: int
    remaining_tickets: int
    is_available: bool
    is_sold_out: bool
    timing: Optional[str] = None

    class Config:
        from_attributes = True

class SportsListResponse(BaseModel):
    total_sports: int
    available_sports: int
    sold_out_sports: int
    sports: List[SportsAvailabilityResponse]

    class Config:
        from_attributes = True

class TicketPurchaseRequest(BaseModel):
    sport_key: str
    quantity: int = 1

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        if v > 10:  # Limit to 10 tickets per purchase
            raise ValueError('Cannot purchase more than 10 tickets at once')
        return v

class TicketPurchaseResponse(BaseModel):
    success: bool
    sport_key: str
    sport_name: str
    quantity: int
    total_price: int
    remaining_tickets: int
    is_sold_out: bool
    message: str
