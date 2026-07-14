"""
SQLAlchemy ORM models for the AI-CRM HCP Module.

Defines the core data models: HCP (Healthcare Professional),
Interaction (engagement records), and Product (pharmaceutical products).
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from database import Base


class HCP(Base):
    """
    Healthcare Professional model.

    Represents a doctor, nurse, or other medical professional
    that the CRM tracks for engagement purposes.

    Attributes:
        id: Primary key.
        name: Full name of the HCP.
        specialty: Medical specialty (e.g. Cardiology, Oncology).
        institution: Hospital or clinic affiliation.
        email: Contact email address.
        phone: Contact phone number.
        territory: Geographic sales territory.
        tier: Engagement tier classification (KOL, High, Medium, Low).
        notes: Free-form notes about the HCP.
        npi_number: National Provider Identifier (optional).
        city: City of practice.
        state: State or region of practice.
        created_at: Timestamp when the record was created.
        updated_at: Timestamp when the record was last updated.
        interactions: Relationship to associated Interaction records.
    """

    __tablename__ = "hcps"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    specialty = Column(String(255), nullable=False)
    institution = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    territory = Column(String(100), nullable=True)
    tier = Column(
        SAEnum("KOL", "High", "Medium", "Low", name="hcp_tier"),
        nullable=False,
        default="Medium",
    )
    notes = Column(Text, nullable=True)
    npi_number = Column(String(20), nullable=True, unique=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    interactions = relationship(
        "Interaction", back_populates="hcp", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<HCP(id={self.id}, name='{self.name}', specialty='{self.specialty}', tier='{self.tier}')>"


class Interaction(Base):
    """
    Interaction model.

    Represents a single engagement event between a sales rep
    and an HCP, including calls, emails, visits, conferences,
    and virtual meetings.

    Attributes:
        id: Primary key.
        hcp_id: Foreign key referencing the associated HCP.
        interaction_type: Type of interaction (call, email, visit, conference, virtual).
        date: Date and time the interaction occurred.
        duration_minutes: Length of the interaction in minutes.
        summary: Brief structured summary of the interaction.
        key_topics: JSON list of key discussion topics.
        products_discussed: JSON list of product names discussed.
        sentiment: Overall sentiment of the interaction (positive, neutral, negative).
        follow_up_required: Whether a follow-up action is needed.
        follow_up_date: Scheduled date for follow-up, if any.
        follow_up_notes: Notes about the planned follow-up.
        logged_by: Name or identifier of the person logging the interaction.
        raw_notes: Original unprocessed notes from the rep.
        ai_summary: AI-generated summary of the interaction.
        created_at: Timestamp when the record was created.
        updated_at: Timestamp when the record was last updated.
        hcp: Relationship to the parent HCP record.
    """

    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hcp_id = Column(Integer, ForeignKey("hcps.id"), nullable=False, index=True)
    interaction_type = Column(
        SAEnum("call", "email", "visit", "conference", "virtual", name="interaction_type_enum"),
        nullable=False,
    )
    date = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    duration_minutes = Column(Integer, nullable=True)
    summary = Column(Text, nullable=True)
    key_topics = Column(JSON, nullable=True, default=list)
    products_discussed = Column(JSON, nullable=True, default=list)
    sentiment = Column(
        SAEnum("positive", "neutral", "negative", name="sentiment_enum"),
        nullable=True,
        default="neutral",
    )
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime, nullable=True)
    follow_up_notes = Column(Text, nullable=True)
    logged_by = Column(String(255), nullable=True)
    raw_notes = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    hcp = relationship("HCP", back_populates="interactions")

    def __repr__(self) -> str:
        return (
            f"<Interaction(id={self.id}, hcp_id={self.hcp_id}, "
            f"type='{self.interaction_type}', date='{self.date}')>"
        )


class Product(Base):
    """
    Product model.

    Represents a pharmaceutical or therapeutic product
    that can be discussed during HCP interactions.

    Attributes:
        id: Primary key.
        name: Brand or generic name of the product.
        therapeutic_area: Therapeutic area the product targets.
        description: Detailed description of the product.
        key_messages: JSON list of approved key marketing messages.
        status: Current product lifecycle status (active, pipeline, discontinued).
        created_at: Timestamp when the record was created.
        updated_at: Timestamp when the record was last updated.
    """

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    therapeutic_area = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    key_messages = Column(JSON, nullable=True, default=list)
    status = Column(
        SAEnum("active", "pipeline", "discontinued", name="product_status_enum"),
        nullable=False,
        default="active",
    )
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}', status='{self.status}')>"
