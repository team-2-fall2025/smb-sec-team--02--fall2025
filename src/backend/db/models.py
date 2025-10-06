# src/backend/db/models.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict

class Asset(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    name: str
    type: str  # HW/SW/Data/User/Service
    criticality: int = 2

class IntelEvent(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    source: str  # shodan/otx/virustotal...
    indicator: str
    raw: Dict
    severity: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RiskItem(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    asset_id: Optional[str]
    title: str
    likelihood: int
    impact: int
