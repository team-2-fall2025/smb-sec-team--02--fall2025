from datetime import datetime
from typing import Literal, Optional, List, Dict, Any

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

class ApplicabilityRule(BaseModel):
    """Flexible JSON logic or tag-based rule"""
    tags: Optional[List[str]] = None
    criticality_gte: Optional[int] = None
    environment: Optional[List[str]] = None
    data_classification: Optional[List[str]] = None
    custom: Optional[Dict[str, Any]] = None  # For JSON Logic expressions

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

class RiskItem(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    title: str
    asset_id: PyObjectId
    status: str = "Open"
    owner: str = "unassigned"  # From asset.owner
    due: datetime
    score: int  # e.g., asset.criticality * sev
    hit_count: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }

class Detection(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id", coerce_types=True)
    asset_id: PyObjectId = Field(..., coerce_types=True)
    source: str  # e.g., "shodan"
    indicator: str  # e.g., "203.0.113.10"
    ttp: List[str] = []  # e.g., ["T1190"]
    severity: int  # 1-5
    confidence: int  # 0-100
    first_seen: datetime
    last_seen: datetime
    hit_count: int = 1
    analyst_note: str  # ≤240 chars
    raw_ref: dict  # e.g., {"intel_ids": ["id1"]}
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }
    
class Control(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    family: str = Field(..., example="AC")  # e.g., AC, AU, SC, CM
    control_id: str = Field(..., example="AC-2")  # e.g., AC-2, IA-5(1)
    title: str = Field(..., example="Account Management")
    csf_function: Literal[
        "Identify", "Protect", "Detect", "Respond", "Recover", "Govern"
    ]
    csf_category: str = Field(..., example="PR.AC")  # e.g., PR.AC, PR.DS
    subcategory: Optional[str] = Field(None, example="PR.AC-1")
    applicability_rule: ApplicabilityRule
    implementation_status: Literal["Proposed", "In-Progress", "Implemented", "Declined"] = "Proposed"
    evidence_required: List[str] = Field(
        default_factory=list,
        example=["Configuration screenshot", "Audit log extract"]
    )
    sop_id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")  # References SOP document
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


# =============================================================================
# 2. Policies (optional this week – container for bundles)
# =============================================================================
class Policy(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., example="SMB Baseline Security Policy")
    description: Optional[str] = None
    scope: Dict[str, Any] = Field(
        default_factory=dict,
        description="org, BU, tags, etc.",
        example={"org_id": "org_123", "tags": ["internet-facing"]}
    )
    status: Literal["Draft", "Active", "Archived"] = "Draft"
    version: str = Field(default="1.0.0")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


# =============================================================================
# 3. Control Mappings (CSF → NIST 800-53)
# =============================================================================
class ControlMapping(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    control_id: str = Field(..., example="IA-2")  # Links to Control.control_id
    csf_ref: str = Field(
        ..., example="Protect/PR.AC-1", description="function/category/subcategory"
    )
    references: List[str] = Field(
        default_factory=list,
        example=["CIS 1.4", "ISO 27001 A.9.2.1"]
    )
    rationale: str = Field(..., example="Enforces strong authentication for privileged access")

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


# =============================================================================
# 4. Policy Assignments (which assets have which controls)
# =============================================================================
class PolicyAssignment(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    asset_id: PyObjectId = Field(...)
    control_id: str = Field(..., example="IA-2")  # Denormalized for fast queries
    policy_id: Optional[PyObjectId] = None  # Optional link to bundle
    status: Literal["Proposed", "In-Progress", "Implemented", "Not Applicable"] = "Proposed"
    owner: str = Field(..., example="jane.doe@company.com")
    due_date: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


# =============================================================================
# 5. Control Evidence (metadata only this week)
# =============================================================================
class ControlEvidence(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    control_id: str = Field(..., example="IA-2")
    asset_id: Optional[PyObjectId] = None  # Nullable – can be org-wide
    evidence_type: Literal[
        "screenshot", "config", "log_extract", "policy_doc", "test_result", "other"
    ]
    location: str = Field(
        ..., example="/evidence/550e8400-e29b-41d4-a716-446655440000"
    )
    hash: Optional[str] = None  # SHA256 for integrity later
    submitted_by: str = Field(..., example="john.doe@company.com")
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

    notes: Optional[str] = None

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


# =============================================================================
# Optional: SOP Document Model (if stored separately)
# =============================================================================
class SOP(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    control_id: str
    title: str
    markdown_content: str  # Full SOP in Markdown
    version: str = "1.0"
    owner: str
    cadence: str  # e.g., "One-time + quarterly verification"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}