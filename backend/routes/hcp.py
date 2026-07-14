"""
HCP API routes for the AI-CRM HCP Module.

Provides endpoints for listing, retrieving, and creating
Healthcare Professional records.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import HCP, Interaction
from schemas import HCPCreate, HCPResponse, HCPDetailResponse, HCPUpdate

router = APIRouter(prefix="/api/hcps", tags=["HCPs"])


def _compute_engagement_score(interactions: list[Interaction]) -> float:
    """
    Compute a simple engagement score (0-100) based on interaction
    recency, frequency, and sentiment.
    """
    if not interactions:
        return 0.0

    now = datetime.now(timezone.utc)
    score = 0.0

    # Frequency component (max 40 points)
    score += min(len(interactions) * 8, 40)

    # Recency component (max 30 points)
    most_recent = max(
        (i.date for i in interactions if i.date),
        default=None,
    )
    if most_recent:
        if most_recent.tzinfo is None:
            most_recent = most_recent.replace(tzinfo=timezone.utc)
        days_since = (now - most_recent).days
        if days_since <= 7:
            score += 30
        elif days_since <= 14:
            score += 25
        elif days_since <= 30:
            score += 18
        elif days_since <= 60:
            score += 10
        else:
            score += 3

    # Sentiment component (max 30 points)
    sentiment_map = {"positive": 10, "neutral": 5, "negative": 1}
    sentiment_total = sum(
        sentiment_map.get(i.sentiment, 5) for i in interactions
    )
    sentiment_avg = sentiment_total / len(interactions)
    score += min(sentiment_avg * 3, 30)

    return round(min(score, 100.0), 1)


@router.get("/", response_model=list[HCPResponse])
def list_hcps(
    specialty: Optional[str] = Query(None, description="Filter by specialty"),
    tier: Optional[str] = Query(None, description="Filter by tier (KOL, High, Medium, Low)"),
    territory: Optional[str] = Query(None, description="Filter by territory"),
    search: Optional[str] = Query(None, description="Search by name or institution"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    db: Session = Depends(get_db),
):
    """
    List all Healthcare Professionals with optional filters.

    Supports filtering by specialty, tier, territory, and a
    free-text search across name and institution. Results are
    ordered by name and paginated.

    Args:
        specialty: Optional specialty filter.
        tier: Optional tier filter.
        territory: Optional territory filter.
        search: Optional free-text search string.
        skip: Pagination offset.
        limit: Pagination limit.
        db: Database session (injected).

    Returns:
        List of matching HCP records.
    """
    query = db.query(HCP)

    if specialty is not None:
        query = query.filter(HCP.specialty.ilike(f"%{specialty}%"))

    if tier is not None:
        query = query.filter(HCP.tier == tier)

    if territory is not None:
        query = query.filter(HCP.territory.ilike(f"%{territory}%"))

    if search is not None:
        query = query.filter(
            (HCP.name.ilike(f"%{search}%")) | (HCP.institution.ilike(f"%{search}%"))
        )

    hcps = query.order_by(HCP.name).offset(skip).limit(limit).all()
    return hcps


@router.get("/{hcp_id}", response_model=HCPDetailResponse)
def get_hcp(
    hcp_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve a single HCP by ID with full interaction history and metrics.

    Returns the HCP profile along with all associated interactions,
    total interaction count, computed engagement score, and the date
    of the most recent interaction.

    Args:
        hcp_id: The primary key of the HCP.
        db: Database session (injected).

    Returns:
        HCPDetailResponse with full profile and engagement data.

    Raises:
        HTTPException 404: If no HCP with the given ID exists.
    """
    hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
    if not hcp:
        raise HTTPException(
            status_code=404,
            detail=f"HCP with id {hcp_id} not found.",
        )

    interactions = (
        db.query(Interaction)
        .filter(Interaction.hcp_id == hcp_id)
        .order_by(Interaction.date.desc())
        .all()
    )

    engagement_score = _compute_engagement_score(interactions)

    last_interaction_date = None
    if interactions:
        last_interaction_date = interactions[0].date

    # Build the response
    response = HCPDetailResponse(
        id=hcp.id,
        name=hcp.name,
        specialty=hcp.specialty,
        institution=hcp.institution,
        email=hcp.email,
        phone=hcp.phone,
        territory=hcp.territory,
        tier=hcp.tier,
        notes=hcp.notes,
        npi_number=hcp.npi_number,
        city=hcp.city,
        state=hcp.state,
        created_at=hcp.created_at,
        updated_at=hcp.updated_at,
        interactions=[],
        total_interactions=len(interactions),
        engagement_score=engagement_score,
        last_interaction_date=last_interaction_date,
    )

    # Manually serialize interactions to avoid lazy-loading issues
    from schemas import InteractionResponse

    response.interactions = [
        InteractionResponse.model_validate(i) for i in interactions
    ]

    return response


@router.post("/", response_model=HCPResponse, status_code=201)
def create_hcp(
    payload: HCPCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new Healthcare Professional record.

    Checks for duplicate NPI numbers if provided.

    Args:
        payload: HCPCreate schema with HCP details.
        db: Database session (injected).

    Returns:
        The newly created HCP record.

    Raises:
        HTTPException 409: If an HCP with the same NPI number already exists.
    """
    # Check for duplicate NPI
    if payload.npi_number:
        existing = (
            db.query(HCP)
            .filter(HCP.npi_number == payload.npi_number)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"An HCP with NPI number '{payload.npi_number}' already exists (id={existing.id}).",
            )

    hcp_data = payload.model_dump(exclude_unset=True)
    hcp = HCP(**hcp_data)
    db.add(hcp)
    db.commit()
    db.refresh(hcp)
    return hcp


@router.put("/{hcp_id}", response_model=HCPResponse)
def update_hcp(
    hcp_id: int,
    payload: HCPUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing HCP record.

    Only fields provided in the payload (non-None) will be updated.

    Args:
        hcp_id: The primary key of the HCP to update.
        payload: HCPUpdate schema with fields to change.
        db: Database session (injected).

    Returns:
        The updated HCP record.

    Raises:
        HTTPException 404: If no HCP with the given ID exists.
        HTTPException 409: If the new NPI number conflicts with another HCP.
    """
    hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
    if not hcp:
        raise HTTPException(
            status_code=404,
            detail=f"HCP with id {hcp_id} not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)

    # Check NPI uniqueness if being changed
    if "npi_number" in update_data and update_data["npi_number"]:
        existing = (
            db.query(HCP)
            .filter(HCP.npi_number == update_data["npi_number"], HCP.id != hcp_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"An HCP with NPI number '{update_data['npi_number']}' already exists (id={existing.id}).",
            )

    for field, value in update_data.items():
        setattr(hcp, field, value)

    hcp.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(hcp)
    return hcp
