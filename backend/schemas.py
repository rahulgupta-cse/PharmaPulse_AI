"""
Pydantic schemas for the AI-CRM HCP Module.

Provides request/response validation schemas for all API endpoints,
including HCP, Interaction, Product, and Agent-related schemas.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# Product Schemas
# ---------------------------------------------------------------------------


class ProductBase(BaseModel):
    """Base schema for Product data shared across create and response."""

    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    therapeutic_area: str = Field(
        ..., min_length=1, max_length=255, description="Therapeutic area"
    )
    description: Optional[str] = Field(None, description="Product description")
    key_messages: Optional[list[str]] = Field(
        default_factory=list, description="Approved key marketing messages"
    )
    status: Optional[str] = Field(
        "active",
        pattern="^(active|pipeline|discontinued)$",
        description="Product lifecycle status",
    )


class ProductCreate(ProductBase):
    """Schema for creating a new Product."""

    pass


class ProductResponse(ProductBase):
    """Schema for Product API responses."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# HCP Schemas
# ---------------------------------------------------------------------------


class HCPBase(BaseModel):
    """Base schema for HCP data shared across create and response."""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Full name of the HCP"
    )
    specialty: str = Field(
        ..., min_length=1, max_length=255, description="Medical specialty"
    )
    institution: Optional[str] = Field(
        None, max_length=255, description="Hospital or clinic"
    )
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    territory: Optional[str] = Field(
        None, max_length=100, description="Sales territory"
    )
    tier: Optional[str] = Field(
        "Medium",
        pattern="^(KOL|High|Medium|Low)$",
        description="Engagement tier",
    )
    notes: Optional[str] = Field(None, description="Free-form notes")
    npi_number: Optional[str] = Field(
        None, max_length=20, description="National Provider Identifier"
    )
    city: Optional[str] = Field(None, max_length=100, description="City of practice")
    state: Optional[str] = Field(None, max_length=100, description="State or region")


class HCPCreate(HCPBase):
    """Schema for creating a new HCP record."""

    pass


class HCPUpdate(BaseModel):
    """Schema for partially updating an existing HCP record."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    specialty: Optional[str] = Field(None, min_length=1, max_length=255)
    institution: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    territory: Optional[str] = Field(None, max_length=100)
    tier: Optional[str] = Field(None, pattern="^(KOL|High|Medium|Low)$")
    notes: Optional[str] = None
    npi_number: Optional[str] = Field(None, max_length=20)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)


class HCPResponse(HCPBase):
    """Schema for HCP API responses."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HCPDetailResponse(HCPResponse):
    """
    Extended HCP response that includes interaction history
    and computed engagement metrics.
    """

    interactions: list["InteractionResponse"] = Field(
        default_factory=list, description="Interaction history"
    )
    total_interactions: int = Field(0, description="Total number of interactions")
    engagement_score: float = Field(
        0.0, description="Computed engagement score (0-100)"
    )
    last_interaction_date: Optional[datetime] = Field(
        None, description="Date of most recent interaction"
    )


# ---------------------------------------------------------------------------
# Interaction Schemas
# ---------------------------------------------------------------------------


class InteractionBase(BaseModel):
    """Base schema for Interaction data."""

    hcp_id: int = Field(..., description="Foreign key to the HCP")
    interaction_type: str = Field(
        ...,
        pattern="^(call|email|visit|conference|virtual)$",
        description="Type of interaction",
    )
    date: Optional[datetime] = Field(None, description="Date/time of interaction")
    duration_minutes: Optional[int] = Field(
        None, ge=0, description="Duration in minutes"
    )
    summary: Optional[str] = Field(None, description="Structured summary")
    key_topics: Optional[list[str]] = Field(
        default_factory=list, description="Key discussion topics"
    )
    products_discussed: Optional[list[str]] = Field(
        default_factory=list, description="Products discussed"
    )
    sentiment: Optional[str] = Field(
        "neutral",
        pattern="^(positive|neutral|negative)$",
        description="Overall sentiment",
    )
    follow_up_required: Optional[bool] = Field(
        False, description="Whether follow-up is needed"
    )
    follow_up_date: Optional[datetime] = Field(
        None, description="Scheduled follow-up date"
    )
    follow_up_notes: Optional[str] = Field(None, description="Follow-up notes")
    logged_by: Optional[str] = Field(
        None, max_length=255, description="Person logging"
    )
    raw_notes: Optional[str] = Field(None, description="Original raw notes")


class InteractionCreate(InteractionBase):
    """Schema for creating a new Interaction."""

    pass


class InteractionUpdate(BaseModel):
    """Schema for partially updating an existing Interaction."""

    hcp_id: Optional[int] = None
    interaction_type: Optional[str] = Field(
        None, pattern="^(call|email|visit|conference|virtual)$"
    )
    date: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=0)
    summary: Optional[str] = None
    key_topics: Optional[list[str]] = None
    products_discussed: Optional[list[str]] = None
    sentiment: Optional[str] = Field(
        None, pattern="^(positive|neutral|negative)$"
    )
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[datetime] = None
    follow_up_notes: Optional[str] = None
    logged_by: Optional[str] = None
    raw_notes: Optional[str] = None
    ai_summary: Optional[str] = None


class InteractionResponse(InteractionBase):
    """Schema for Interaction API responses."""

    id: int
    ai_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Agent / Chat Schemas
# ---------------------------------------------------------------------------


class ChatMessage(BaseModel):
    """Schema for a chat message sent to the AI agent."""

    message: str = Field(
        ..., min_length=1, description="The user's natural-language message"
    )
    hcp_id: Optional[int] = Field(
        None, description="Optional HCP context for the conversation"
    )


class ProcessNotesRequest(BaseModel):
    """Schema for the process-notes endpoint."""

    raw_notes: str = Field(
        ..., min_length=1, description="Raw interaction notes to process"
    )
    hcp_id: Optional[int] = Field(None, description="Optional HCP context")
    interaction_type: Optional[str] = Field(
        None,
        pattern="^(call|email|visit|conference|virtual)$",
        description="Type of interaction",
    )


class AgentResponse(BaseModel):
    """Schema for the AI agent's response."""

    response: str = Field(..., description="Agent's natural-language response")
    tool_calls: Optional[list[dict]] = Field(
        default_factory=list, description="Tools the agent invoked"
    )
    data: Optional[dict] = Field(
        None, description="Structured data returned by agent tools"
    )
    error: Optional[str] = Field(
        None, description="Error message if something went wrong"
    )


class ToolInfo(BaseModel):
    """Schema describing an available agent tool."""

    name: str = Field(..., description="Tool function name")
    description: str = Field(..., description="What the tool does")


# Rebuild forward references so HCPDetailResponse can use InteractionResponse
HCPDetailResponse.model_rebuild()
