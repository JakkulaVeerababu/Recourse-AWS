from pydantic import BaseModel, Field
from typing import Optional, Literal

class ApprovalDecision(BaseModel):
    decision: Literal['APPROVE', 'REJECT']
    reason: Optional[str] = Field(None, max_length=1024)
