from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# Input validation for creating a transaction
class TransactionCreate(BaseModel):
    amount: float = Field(..., gt=0, description="Amount must be greater than 0")
    type: str = Field(..., pattern="^(Income|Expense)$")
    category: str = Field(..., min_length=2)
    description: Optional[str] = None

# Output formatting
class TransactionResponse(TransactionCreate):
    id: int
    date: datetime

    class Config:
        from_attributes = True