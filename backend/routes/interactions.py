"""
Interaction API routes for the AI-CRM HCP Module.

Provides CRUD endpoints for managing HCP interaction records.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Interaction, HCP
from schemas import InteractionCreate, InteractionUpdate, InteractionResponse

router = APIRouter(prefix="/api/interactions", tags=["Interactions"])


@router.post("/", response_model=InteractionResponse, status_code=201)
def create_interaction(
    payload: InteractionCreate,
    db: Session = Depends(get_db),
):
    """
    Log a new interaction with an HCP.

    Validates that the referenced HCP exists, then creates and
    persists the interaction record.

    Args:
        payload: InteractionCreate schema with interaction details.
        db: Database session (injected).

    Returns:
        The newly created Interaction record.

    Raises:
        HTTPException 404: If the referenced HCP does not exist.
    """
    # Validate HCP exists
    hcp = db.query(HCP).filter(HCP.id == payload.hcp_id).first()
    if not hcp:
        raise HTTPException(
            status_code=404,
            detail=f"HCP with id {payload.hcp_id} not found.",
        )

    interaction_data = payload.model_dump(exclude_unset=True)

    # Set default date if not provided
    if "date" not in interaction_data or interaction_data["date"] is None:
        interaction_data["date"] = datetime.now(timezone.utc)

    interaction = Interaction(**interaction_data)
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


@router.get("/", response_model=list[InteractionResponse])
def list_interactions(
    hcp_id: Optional[int] = Query(None, description="Filter by HCP ID"),
    interaction_type: Optional[str] = Query(
        None,
        description="Filter by type (call, email, visit, conference, virtual)",
    ),
    sentiment: Optional[str] = Query(
        None, description="Filter by sentiment (positive, neutral, negative)"
    ),
    follow_up_required: Optional[bool] = Query(
        None, description="Filter by follow-up status"
    ),
    date_from: Optional[str] = Query(
        None, description="Start date filter (ISO format YYYY-MM-DD)"
    ),
    date_to: Optional[str] = Query(
        None, description="End date filter (ISO format YYYY-MM-DD)"
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    db: Session = Depends(get_db),
):
    """
    List all interactions with optional filters.

    Supports filtering by HCP, interaction type, sentiment,
    follow-up status, and date range. Results are ordered
    by date descending and paginated.

    Args:
        hcp_id: Optional HCP ID filter.
        interaction_type: Optional interaction type filter.
        sentiment: Optional sentiment filter.
        follow_up_required: Optional follow-up status filter.
        date_from: Optional start date filter.
        date_to: Optional end date filter.
        skip: Pagination offset.
        limit: Pagination limit.
        db: Database session (injected).

    Returns:
        List of matching Interaction records.
    """
    query = db.query(Interaction)

    if hcp_id is not None:
        query = query.filter(Interaction.hcp_id == hcp_id)

    if interaction_type is not None:
        query = query.filter(Interaction.interaction_type == interaction_type)

    if sentiment is not None:
        query = query.filter(Interaction.sentiment == sentiment)

    if follow_up_required is not None:
        query = query.filter(Interaction.follow_up_required == follow_up_required)

    if date_from is not None:
        try:
            dt_from = datetime.fromisoformat(date_from)
            query = query.filter(Interaction.date >= dt_from)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date_from format: '{date_from}'. Use ISO format YYYY-MM-DD.",
            )

    if date_to is not None:
        try:
            dt_to = datetime.fromisoformat(date_to)
            query = query.filter(Interaction.date <= dt_to)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date_to format: '{date_to}'. Use ISO format YYYY-MM-DD.",
            )

    interactions = (
        query.order_by(Interaction.date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return interactions


@router.get("/{interaction_id}", response_model=InteractionResponse)
def get_interaction(
    interaction_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve a single interaction by its ID.

    Args:
        interaction_id: The primary key of the interaction.
        db: Database session (injected).

    Returns:
        The matching Interaction record.

    Raises:
        HTTPException 404: If no interaction with the given ID exists.
    """
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(
            status_code=404,
            detail=f"Interaction with id {interaction_id} not found.",
        )
    return interaction


@router.put("/{interaction_id}", response_model=InteractionResponse)
def update_interaction(
    interaction_id: int,
    payload: InteractionUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing interaction record.

    Only fields provided in the payload (non-None) will be updated.

    Args:
        interaction_id: The primary key of the interaction to update.
        payload: InteractionUpdate schema with fields to change.
        db: Database session (injected).

    Returns:
        The updated Interaction record.

    Raises:
        HTTPException 404: If no interaction with the given ID exists.
        HTTPException 404: If the new hcp_id does not reference a valid HCP.
    """
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(
            status_code=404,
            detail=f"Interaction with id {interaction_id} not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)

    # Validate HCP if being changed
    if "hcp_id" in update_data:
        hcp = db.query(HCP).filter(HCP.id == update_data["hcp_id"]).first()
        if not hcp:
            raise HTTPException(
                status_code=404,
                detail=f"HCP with id {update_data['hcp_id']} not found.",
            )

    for field, value in update_data.items():
        setattr(interaction, field, value)

    interaction.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(interaction)
    return interaction


@router.delete("/{interaction_id}", status_code=204)
def delete_interaction(
    interaction_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete an interaction record.

    Args:
        interaction_id: The primary key of the interaction to delete.
        db: Database session (injected).

    Raises:
        HTTPException 404: If no interaction with the given ID exists.
    """
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(
            status_code=404,
            detail=f"Interaction with id {interaction_id} not found.",
        )

    db.delete(interaction)
    db.commit()
    return None
