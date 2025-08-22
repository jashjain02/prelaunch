from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class OrangetheoryRegistrationSchema(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    selected_sports: List[str]
    orangetheory_batch: Optional[str] = None
    event_date: Optional[str] = None
    event_location: Optional[str] = None
    payment_status: Optional[str] = "pending"
    file_url: Optional[str] = None
    is_active: Optional[bool] = True

class OrangetheoryRegistrationResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    phone: str
    selected_sports: str
    orangetheory_batch: Optional[str] = None
    event_date: Optional[str] = None
    event_location: Optional[str] = None
    payment_status: str
    file_url: Optional[str] = None
    booking_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OrangetheoryRegistrationListResponse(BaseModel):
    registrations: List[OrangetheoryRegistrationResponse]
    total: int
    skip: int
    limit: int
