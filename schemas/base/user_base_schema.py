from typing import List, Optional
from pydantic import BaseModel
from schemas.login_schema import LoginSchema

class UserBaseSchema(LoginSchema):
    id: int
    role: Optional[List[str]]