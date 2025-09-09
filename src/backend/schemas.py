from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProviderEnum(str, Enum):
    openai = "openai"
    gemini = "gemini"
    deepseek = "deepseek"
    mock = "mock"


class Card(BaseModel):
    """Single UI card unit used by the frontend."""

    id: str = Field(..., description="Stable identifier for the card")
    title: str = Field(..., description="Short title for the card")
    content: str = Field(..., description="Primary text content for the card")
    kind: Optional[str] = Field(
        default="text",
        description="Optional content kind (e.g., text, code, note).",
    )


class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="User prompt or task request")
    provider: Optional[ProviderEnum] = Field(
        default=None, description="LLM provider to use"
    )
    model: Optional[str] = Field(
        default=None, description="Model name override for the chosen provider"
    )
    system: Optional[str] = Field(
        default=None, description="Optional additional system instruction"
    )
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int = Field(default=800, ge=1)


class UsageInfo(BaseModel):
    provider: str
    model: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: Optional[int] = None


class GenerateResponse(BaseModel):
    cards: List[Card]
    usage: UsageInfo
    raw_text: Optional[str] = Field(
        default=None, description="Raw model text in case JSON parsing failed"
    )
    meta: Dict[str, Any] = Field(default_factory=dict)


class FollowupRequest(BaseModel):
    current_card_title: str
    current_card_content: str
    question: str
    provider: Optional[ProviderEnum] = None
    model: Optional[str] = None
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int = Field(default=400, ge=1)


class FollowupResponse(BaseModel):
    card: Card
    usage: UsageInfo
    raw_text: Optional[str] = None


class ErrorResponse(BaseModel):
    detail: str
    error_type: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
