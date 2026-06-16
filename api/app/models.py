from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


CONTRACT_VERSION = "1.0"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SCORED = "scored"
    FAILED = "failed"


class TransactionType(str, Enum):
    CREDIT = "credit"
    DEBIT = "debit"


class TransactionIngest(BaseModel):
    contract_version: str
    transaction_id: str
    user_id: int = Field(..., gt=0)
    amount: float = Field(..., gt=0)
    type: TransactionType
    merchant: str = Field(..., min_length=1)


class ScoreResult(BaseModel):
    contract_version: str
    transaction_id: str
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: str
    reasons: list[str]


class Transaction(BaseModel):
    contract_version: str
    transaction_id: str
    user_id: int
    amount: float
    type: TransactionType
    merchant: str
    status: TransactionStatus
    score: Optional[ScoreResult] = None
