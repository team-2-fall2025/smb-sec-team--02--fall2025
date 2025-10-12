from datetime import datetime
from typing import Optional, List, Dict, Any

from bson import ObjectId
from pydantic import BaseModel, Field, GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic_core import CoreSchema, core_schema
from pydantic.json_schema import JsonSchemaValue


# ---------------------------
# ObjectId 类型兼容
# ---------------------------
class PyObjectId(ObjectId):
    """为 MongoDB ObjectId 添加 Pydantic 支持（兼容 v2）"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """用于 Pydantic v2 序列化支持"""
        return core_schema.no_info_after_validator_function(
            cls.validate, core_schema.str_schema()
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        """告诉 OpenAPI 它是 string 类型"""
        json_schema = handler(core_schema)
        json_schema.update(type="string")
        return json_schema


# ---------------------------
# 资产表 (assets)
# ---------------------------
class Asset(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    type: str  # HW, SW, Data, User, Service
    ip: Optional[str] = None
    hostname: Optional[str] = None
    owner: Optional[str] = None
    business_unit: Optional[str] = None
    criticality: int = Field(default=1, ge=1, le=5)
    data_sensitivity: str = Field(default="Low")  # Low, Moderate, High
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }


# ---------------------------
# 情报事件表 (intel_events)
# ---------------------------
class IntelEvent(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    source: str  # otx, shodan, etc.
    event_type: str  # malware, threat_intel, etc.
    indicator: str  # IP/domain/hash
    indicator_type: str  # ipv4/domain/md5/sha256
    severity: int = Field(ge=0, le=5)  # 数值等级 1~5
    confidence: float = Field(ge=0.0, le=1.0)
    description: Optional[str] = None
    raw_data: Dict[str, Any] = {}
    tags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }


# ---------------------------
# 资产-情报关联表 (asset_intel_links)
# ---------------------------
class AssetIntelLink(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    asset_id: PyObjectId
    intel_id: PyObjectId
    match_type: str  # ip | domain | hostname
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }


# ---------------------------
# （可选）风险项表 (risk_items)
# ---------------------------
class RiskItem(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    asset_id: PyObjectId
    intel_event_id: Optional[PyObjectId] = None
    risk_score: Optional[float] = None
    description: Optional[str] = None
    status: str = "open"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }
