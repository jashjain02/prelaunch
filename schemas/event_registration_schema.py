from pydantic import BaseModel, EmailStr
from typing import List, Optional

class EventRegistrationSchema(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    selected_sports: List[str]
    pickleball_level: Optional[str] = None 