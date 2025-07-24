from pydantic import BaseModel
from typing import Optional

class TransactionSchema(BaseModel):
    event_registration_id: int
    amount: float
    status: str
    razorpay_payment_id: Optional[str] = None 