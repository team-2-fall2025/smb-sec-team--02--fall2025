from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        field_schema = handler(core_schema)
        field_schema.update(type="string")
        return field_schema

class Asset(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str
    asset_type: str  # ip, domain, url, etc.
    value: str
    description: Optional[str] = None
    tags: list[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,  # Updated from allow_population_by_field_name
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

class IntelEvent(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    source: str  # otx, shodan, censys, etc.
    event_type: str  # malware, ioc, threat_intel, etc.
    indicator: str  # ip, domain, hash, etc.
    indicator_type: str  # ipv4, domain, md5, sha256, etc.
    confidence: float = Field(ge=0.0, le=1.0)  # 0.0 to 1.0
    severity: str  # low, medium, high, critical
    description: str
    raw_data: Dict[str, Any]  # Original API response
    tags: list[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,  # Updated from allow_population_by_field_name
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

class RiskItem(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    asset_id: Optional[PyObjectId] = None
    intel_event_id: Optional[PyObjectId] = None
    risk_type: str  # vulnerability, threat, compliance, etc.
    risk_level: str  # low, medium, high, critical
    score: float = Field(ge=0.0, le=10.0)  # 0.0 to 10.0
    description: str
    mitigation: Optional[str] = None
    status: str = "open"  # open, in_progress, resolved, false_positive
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,  # Updated from allow_population_by_field_name
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }