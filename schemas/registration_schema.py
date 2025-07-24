from pydantic import BaseModel
from typing import Optional, List

class RegistrationSchema(BaseModel):
    first_name: str
    last_name: str
    email: str
    contact_number: Optional[str] = None