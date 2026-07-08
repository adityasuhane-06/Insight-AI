"""
Pydantic request/response schemas.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl, field_validator


# ─── Session Schemas ───────────────────────────────────────────────

class SessionCreate(BaseModel):
    company_name: str
    website: str
    objective: str

    @field_validator("company_name")
    @classmethod
    def company_name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Company name cannot be empty")
        return v.strip()

    @field_validator("objective")
    @classmethod
    def objective_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Research objective cannot be empty")
        return v.strip()


class ChatMessageOut(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionOut(BaseModel):
    id: str
    company_name: str
    website: str
    objective: str
    status: str
    current_node: str
    error_message: str
    report_markdown: str
    report_json: str
    retry_count: int
    quality_score: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionListItem(BaseModel):
    id: str
    company_name: str
    website: str
    objective: str
    status: str
    quality_score: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Chat Schemas ──────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()


class ChatResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime


# ─── SSE Event Schemas ─────────────────────────────────────────────

class WorkflowEvent(BaseModel):
    type: str          # "progress" | "complete" | "error" | "log"
    node: Optional[str] = None
    message: Optional[str] = None
    data: Optional[dict] = None
