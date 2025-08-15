from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class UserRegistrationBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    jgu_student_id: str
    city: str
    state: str
    agreed_to_terms: bool = True

    @validator('first_name', 'last_name', 'city')
    def validate_name_fields(cls, v):
        if not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()

    @validator('phone')
    def validate_phone(cls, v):
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, v))
        if len(digits_only) != 10:
            raise ValueError('Phone number must be 10 digits')
        return v

    @validator('jgu_student_id')
    def validate_student_id(cls, v):
        if not v.strip():
            raise ValueError('JGU Student ID cannot be empty')
        return v.strip()

    @validator('state')
    def validate_state(cls, v):
        valid_states = [
            "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
            "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
            "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
            "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
            "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
            "West Bengal", "Delhi", "Jammu and Kashmir", "Ladakh", "Chandigarh",
            "Dadra and Nagar Haveli and Daman and Diu", "Lakshadweep", "Puducherry",
            "Andaman and Nicobar Islands"
        ]
        if v not in valid_states:
            raise ValueError('Invalid state selected')
        return v

class UserRegistrationCreate(UserRegistrationBase):
    pass

class UserRegistrationResponse(UserRegistrationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserRegistrationUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    jgu_student_id: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    agreed_to_terms: Optional[bool] = None
