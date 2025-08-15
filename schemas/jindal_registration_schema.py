from pydantic import BaseModel, validator, EmailStr
from typing import Optional, List
from datetime import datetime
import json

class JindalRegistrationBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    jgu_student_id: str
    city: str
    state: str
    selected_sports: Optional[List[str]] = []
    pickle_level: Optional[str] = None
    total_amount: int = 0
    payment_status: str = "pending"
    payment_proof: Optional[str] = None
    agreed_to_terms: bool = True

    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        return v.strip()

    @validator('phone')
    def validate_phone(cls, v):
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, v))
        if len(digits_only) != 10:
            raise ValueError('Phone number must be exactly 10 digits')
        return digits_only

    @validator('jgu_student_id')
    def validate_jgu_id(cls, v):
        if not v.strip():
            raise ValueError('JGU Student ID cannot be empty')
        if len(v.strip()) < 3:
            raise ValueError('JGU Student ID must be at least 3 characters long')
        return v.strip().upper()

    @validator('city')
    def validate_city(cls, v):
        if not v.strip():
            raise ValueError('City cannot be empty')
        return v.strip()

    @validator('state')
    def validate_state(cls, v):
        indian_states = [
            "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
            "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
            "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
            "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
            "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
            "Uttar Pradesh", "Uttarakhand", "West Bengal",
            "Delhi", "Jammu and Kashmir", "Ladakh", "Chandigarh",
            "Dadra and Nagar Haveli and Daman and Diu", "Lakshadweep", "Puducherry"
        ]
        if v not in indian_states:
            raise ValueError(f'State must be one of: {", ".join(indian_states)}')
        return v

    @validator('total_amount')
    def validate_total_amount(cls, v):
        if v < 0:
            raise ValueError('Total amount cannot be negative')
        return v

    @validator('payment_status')
    def validate_payment_status(cls, v):
        valid_statuses = ["pending", "completed", "failed"]
        if v not in valid_statuses:
            raise ValueError(f'Payment status must be one of: {", ".join(valid_statuses)}')
        return v

    @validator('pickle_level')
    def validate_pickle_level(cls, v):
        if v is not None:
            valid_levels = ["Beginner", "Intermediate", "Advanced"]
            if v not in valid_levels:
                raise ValueError(f'Pickle level must be one of: {", ".join(valid_levels)}')
        return v

class JindalRegistrationCreate(JindalRegistrationBase):
    pass

class JindalRegistrationUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    jgu_student_id: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    selected_sports: Optional[List[str]] = None
    pickle_level: Optional[str] = None
    total_amount: Optional[int] = None
    payment_status: Optional[str] = None
    payment_proof: Optional[str] = None
    agreed_to_terms: Optional[bool] = None

    @validator('phone')
    def validate_phone(cls, v):
        if v is not None:
            digits_only = ''.join(filter(str.isdigit, v))
            if len(digits_only) != 10:
                raise ValueError('Phone number must be exactly 10 digits')
            return digits_only
        return v

    @validator('jgu_student_id')
    def validate_jgu_id(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError('JGU Student ID cannot be empty')
            if len(v.strip()) < 3:
                raise ValueError('JGU Student ID must be at least 3 characters long')
            return v.strip().upper()
        return v

    @validator('state')
    def validate_state(cls, v):
        if v is not None:
            indian_states = [
                "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
                "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
                "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
                "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
                "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
                "Uttar Pradesh", "Uttarakhand", "West Bengal",
                "Delhi", "Jammu and Kashmir", "Ladakh", "Chandigarh",
                "Dadra and Nagar Haveli and Daman and Diu", "Lakshadweep", "Puducherry"
            ]
            if v not in indian_states:
                raise ValueError(f'State must be one of: {", ".join(indian_states)}')
        return v

    @validator('total_amount')
    def validate_total_amount(cls, v):
        if v is not None and v < 0:
            raise ValueError('Total amount cannot be negative')
        return v

    @validator('payment_status')
    def validate_payment_status(cls, v):
        if v is not None:
            valid_statuses = ["pending", "completed", "failed"]
            if v not in valid_statuses:
                raise ValueError(f'Payment status must be one of: {", ".join(valid_statuses)}')
        return v

    @validator('pickle_level')
    def validate_pickle_level(cls, v):
        if v is not None:
            valid_levels = ["Beginner", "Intermediate", "Advanced"]
            if v not in valid_levels:
                raise ValueError(f'Pickle level must be one of: {", ".join(valid_levels)}')
        return v

class JindalRegistrationResponse(JindalRegistrationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class JindalRegistrationListResponse(BaseModel):
    total_registrations: int
    registrations: List[JindalRegistrationResponse]

    class Config:
        from_attributes = True
