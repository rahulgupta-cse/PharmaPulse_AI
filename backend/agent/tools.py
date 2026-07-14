"""
LangGraph tools for the AI-CRM HCP Agent.

Provides five tools that the LLM agent can invoke:
1. log_interaction — Log a new HCP interaction with AI summarization.
2. edit_interaction — Modify an existing interaction record.
3. get_hcp_profile — Retrieve full HCP profile with engagement metrics.
4. search_interactions — Search and filter past interactions.
5. suggest_next_action — AI-powered next-best-action recommendations.
"""

import json
from datetime import datetime, timezone, timedelta
from typing import Optional

from langchain_core.tools import tool
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from database import get_db_session
from models import HCP, Interaction, Product


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _serialize_interaction(interaction: Interaction) -> dict:
    """Convert an Interaction ORM object to a plain dictionary."""
    return {
        "id": interaction.id,
        "hcp_id": interaction.hcp_id,
        "interaction_type": interaction.interaction_type,
        "date": interaction.date.isoformat() if interaction.date else None,
        "duration_minutes": interaction.duration_minutes,
        "summary": interaction.summary,
        "key_topics": interaction.key_topics or [],
        "products_discussed": interaction.products_discussed or [],
        "sentiment": interaction.sentiment,
        "follow_up_required": interaction.follow_up_required,
        "follow_up_date": interaction.follow_up_date.isoformat() if interaction.follow_up_date else None,
        "follow_up_notes": interaction.follow_up_notes,
        "logged_by": interaction.logged_by,
        "raw_notes": interaction.raw_notes,
        "ai_summary": interaction.ai_summary,
        "created_at": interaction.created_at.isoformat() if interaction.created_at else None,
    }


def _serialize_hcp(hcp: HCP) -> dict:
    """Convert an HCP ORM object to a plain dictionary (without interactions)."""
    return {
        "id": hcp.id,
        "name": hcp.name,
        "specialty": hcp.specialty,
        "institution": hcp.institution,
        "email": hcp.email,
        "phone": hcp.phone,
        "territory": hcp.territory,
        "tier": hcp.tier,
        "notes": hcp.notes,
        "npi_number": hcp.npi_number,
        "city": hcp.city,
        "state": hcp.state,
    }


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
    frequency_score = min(len(interactions) * 8, 40)
    score += frequency_score

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
        sentiment_map.get(i.sentiment, 5)
        for i in interactions
    )
    sentiment_avg = sentiment_total / len(interactions)
    score += min(sentiment_avg * 3, 30)

    return round(min(score, 100.0), 1)


# ---------------------------------------------------------------------------
# Tool 1: log_interaction
# ---------------------------------------------------------------------------


@tool
def log_interaction(
    hcp_id: int,
    interaction_type: str,
    raw_notes: str,
    duration_minutes: Optional[int] = None,
    logged_by: Optional[str] = None,
    follow_up_required: Optional[bool] = False,
    follow_up_notes: Optional[str] = None,
) -> str:
    """Log a new interaction with a Healthcare Professional (HCP).

    Captures the interaction data, uses AI-style extraction to determine
    key topics, products discussed, and sentiment from the raw notes,
    and stores everything in the database.

    Args:
        Args:
        hcp_id: Integer database ID of the HCP. Must be a numeric integer (example: 1, 2, 15). Never pass it as a string like "1".
        interaction_type: One of: call, email, visit, conference, virtual.
        raw_notes: Representative's notes from the interaction.
        duration_minutes: Integer duration in minutes.
        logged_by: Name of the representative logging the interaction.
        follow_up_required: True or False.
    follow_up_notes: Notes for any follow-up.
        interaction_type: Type of interaction — one of: call, email, visit, conference, virtual.
        raw_notes: The representative's raw notes from the interaction.
        duration_minutes: Optional duration of the interaction in minutes.
        logged_by: Optional name or identifier of the person logging.
        follow_up_required: Whether a follow-up is needed (default False).
        follow_up_notes: Optional notes about the planned follow-up.

    Returns:
        JSON string with the created interaction data or an error message.
    """
    db: Session = get_db_session()
    try:
        # Validate HCP exists
        hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
        if not hcp:
            return json.dumps({"error": f"HCP with id {hcp_id} not found."})

        # Validate interaction type
        valid_types = {"call", "email", "visit", "conference", "virtual"}
        if interaction_type not in valid_types:
            return json.dumps({"error": f"Invalid interaction_type '{interaction_type}'. Must be one of {valid_types}."})

        # Extract key topics from raw notes (rule-based extraction)
        topic_keywords = [
            "heart failure", "COPD", "diabetes", "oncology", "immunotherapy",
            "clinical trial", "formulary", "safety", "efficacy", "dosing",
            "patient adherence", "side effects", "real-world evidence",
            "Phase III", "Phase II", "combination therapy", "biomarker",
            "treatment switching", "comorbidity", "payer access",
            "rheumatoid arthritis", "psoriasis", "multiple sclerosis",
            "CAR-T", "checkpoint inhibitor", "weight loss", "HbA1c",
            "NSCLC", "hematologic", "biologic", "JAK inhibitor",
        ]
        notes_lower = raw_notes.lower()
        key_topics = [kw for kw in topic_keywords if kw in notes_lower]
        if not key_topics:
            # Fallback: extract first few meaningful words
            key_topics = ["general discussion"]

        # Extract products discussed
        products = db.query(Product).all()
        products_discussed = [
            p.name for p in products if p.name.lower() in notes_lower
        ]

        # Simple sentiment detection
        positive_words = [
            "great", "excellent", "interested", "excited", "positive",
            "happy", "receptive", "enthusiastic", "satisfied", "good",
            "pleased", "keen", "favorable", "productive", "strong",
        ]
        negative_words = [
            "concern", "worried", "negative", "unhappy", "disappointed",
            "frustrat", "reject", "adverse", "problem", "issue", "decline",
        ]
        pos_count = sum(1 for w in positive_words if w in notes_lower)
        neg_count = sum(1 for w in negative_words if w in notes_lower)

        if pos_count > neg_count:
            sentiment = "positive"
        elif neg_count > pos_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        # Build AI-style summary
        ai_summary = (
            f"{interaction_type.capitalize()} interaction with {hcp.name} ({hcp.specialty}, {hcp.institution}). "
            f"Topics: {', '.join(key_topics)}. "
            f"Products: {', '.join(products_discussed) if products_discussed else 'None mentioned'}. "
            f"Sentiment: {sentiment}. "
            f"Follow-up: {'Required' if follow_up_required else 'Not required'}."
        )

        # Compute follow-up date
        follow_up_date = None
        if follow_up_required:
            follow_up_date = datetime.now(timezone.utc) + timedelta(days=14)

        # Create the interaction record
        interaction = Interaction(
            hcp_id=hcp_id,
            interaction_type=interaction_type,
            date=datetime.now(timezone.utc),
            duration_minutes=duration_minutes,
            summary=ai_summary,
            key_topics=key_topics,
            products_discussed=products_discussed,
            sentiment=sentiment,
            follow_up_required=follow_up_required,
            follow_up_date=follow_up_date,
            follow_up_notes=follow_up_notes,
            logged_by=logged_by,
            raw_notes=raw_notes,
            ai_summary=ai_summary,
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        result = _serialize_interaction(interaction)
        result["message"] = f"Interaction successfully logged for {hcp.name}."
        return json.dumps(result, default=str)

    except Exception as e:
        db.rollback()
        return json.dumps({"error": f"Failed to log interaction: {str(e)}"})
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 2: edit_interaction
# ---------------------------------------------------------------------------


@tool
def edit_interaction(
    interaction_id: int,
    summary: Optional[str] = None,
    key_topics: Optional[list[str]] = None,
    products_discussed: Optional[list[str]] = None,
    sentiment: Optional[str] = None,
    follow_up_required: Optional[bool] = None,
    follow_up_date: Optional[str] = None,
    follow_up_notes: Optional[str] = None,
    duration_minutes: Optional[int] = None,
) -> str:
    """Edit an existing interaction record.

    Validates the changes and updates the specified fields in the database.
    Only provided (non-None) fields will be updated.

    Args:
        interaction_id: The ID of the interaction to edit.
        summary: New summary text.
        key_topics: Updated list of key discussion topics.
        products_discussed: Updated list of products discussed.
        sentiment: Updated sentiment (positive, neutral, or negative).
        follow_up_required: Whether follow-up is needed.
        follow_up_date: New follow-up date in ISO format (YYYY-MM-DD).
        follow_up_notes: Updated follow-up notes.
        duration_minutes: Updated duration in minutes.

    Returns:
        JSON string with the updated interaction data or an error message.
    """
    db: Session = get_db_session()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return json.dumps({"error": f"Interaction with id {interaction_id} not found."})

        # Validate sentiment if provided
        if sentiment is not None:
            valid_sentiments = {"positive", "neutral", "negative"}
            if sentiment not in valid_sentiments:
                return json.dumps({"error": f"Invalid sentiment '{sentiment}'. Must be one of {valid_sentiments}."})

        # Apply updates
        updates_applied = []

        if summary is not None:
            interaction.summary = summary
            updates_applied.append("summary")

        if key_topics is not None:
            interaction.key_topics = key_topics
            updates_applied.append("key_topics")

        if products_discussed is not None:
            interaction.products_discussed = products_discussed
            updates_applied.append("products_discussed")

        if sentiment is not None:
            interaction.sentiment = sentiment
            updates_applied.append("sentiment")

        if follow_up_required is not None:
            interaction.follow_up_required = follow_up_required
            updates_applied.append("follow_up_required")

        if follow_up_date is not None:
            try:
                interaction.follow_up_date = datetime.fromisoformat(follow_up_date)
            except ValueError:
                return json.dumps({"error": f"Invalid follow_up_date format: '{follow_up_date}'. Use ISO format (YYYY-MM-DD)."})
            updates_applied.append("follow_up_date")

        if follow_up_notes is not None:
            interaction.follow_up_notes = follow_up_notes
            updates_applied.append("follow_up_notes")

        if duration_minutes is not None:
            interaction.duration_minutes = duration_minutes
            updates_applied.append("duration_minutes")

        if not updates_applied:
            return json.dumps({"message": "No fields were provided for update."})

        interaction.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(interaction)

        result = _serialize_interaction(interaction)
        result["message"] = f"Interaction {interaction_id} updated. Fields changed: {', '.join(updates_applied)}."
        return json.dumps(result, default=str)

    except Exception as e:
        db.rollback()
        return json.dumps({"error": f"Failed to edit interaction: {str(e)}"})
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 3: get_hcp_profile
# ---------------------------------------------------------------------------


@tool
def get_hcp_profile(
    hcp_id: Optional[int] = None,
    hcp_name: Optional[str] = None,
) -> str:
    """Retrieve a full HCP profile including interaction history and engagement metrics.

    Looks up the HCP by ID or name and returns their profile data,
    complete interaction history, product affinity analysis, and
    a computed engagement score.

    Args:
        hcp_id: The database ID of the HCP. Use this if you know the ID.
        hcp_name: The name (or partial name) of the HCP. Used for search if ID is not known.

    Returns:
        JSON string with the full HCP profile, interactions, and metrics.
    """
    db: Session = get_db_session()
    try:
        hcp = None

        if hcp_id:
            hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
        elif hcp_name:
            matches = (
                db.query(HCP)
                .filter(HCP.name.ilike(f"%{hcp_name}%"))
                .all()
            )

            if len(matches) == 0:
                return json.dumps({
                    "error": f"No Healthcare Professional found for '{hcp_name}'."
                })

            if len(matches) > 1:

                return json.dumps({

                    "multiple_matches": True,

                    "message": "Multiple Healthcare Professionals found.",

                    "matches": [
                        {
                            "id": h.id,
                            "name": h.name,
                            "specialty": h.specialty,
                            "hospital": h.institution,
                            "city": h.city,
                        }
                        for h in matches
                    ]

                })

            hcp = matches[0]

        if not hcp:
            search_term = hcp_id if hcp_id else hcp_name
            return json.dumps({"error": f"HCP not found for: {search_term}"})

        interactions = (
            db.query(Interaction)
            .filter(Interaction.hcp_id == hcp.id)
            .order_by(Interaction.date.desc())
            .all()
        )

        # Compute engagement score
        engagement_score = _compute_engagement_score(interactions)

        # Product affinity analysis
        product_frequency: dict[str, int] = {}
        for inter in interactions:
            for product in (inter.products_discussed or []):
                product_frequency[product] = product_frequency.get(product, 0) + 1

        # Last interaction date
        last_interaction_date = None
        if interactions:
            last_interaction_date = interactions[0].date.isoformat() if interactions[0].date else None

        # Interaction type breakdown
        type_breakdown: dict[str, int] = {}
        for inter in interactions:
            itype = inter.interaction_type or "unknown"
            type_breakdown[itype] = type_breakdown.get(itype, 0) + 1

        # Sentiment breakdown
        sentiment_breakdown: dict[str, int] = {}
        for inter in interactions:
            sent = inter.sentiment or "neutral"
            sentiment_breakdown[sent] = sentiment_breakdown.get(sent, 0) + 1

        profile = {
            "hcp": _serialize_hcp(hcp),
            "engagement_score": engagement_score,
            "total_interactions": len(interactions),
            "last_interaction_date": last_interaction_date,
            "product_affinity": product_frequency,
            "interaction_type_breakdown": type_breakdown,
            "sentiment_breakdown": sentiment_breakdown,
            "interactions": [_serialize_interaction(i) for i in interactions],
        }

        return json.dumps(profile, default=str)

    except Exception as e:
        return json.dumps({"error": f"Failed to retrieve HCP profile: {str(e)}"})
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 4: search_interactions
# ---------------------------------------------------------------------------


@tool
def search_interactions(
    hcp_id: Optional[int] = None,
    hcp_name: Optional[str] = None,
    interaction_type: Optional[str] = None,
    sentiment: Optional[str] = None,
    product: Optional[str] = None,
    topic: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: Optional[int] = 20,
) -> str:
    """Search past interactions with various filters and get analytics.

    Allows filtering by HCP, date range, interaction type, sentiment,
    product, or topic. Returns matching interactions along with
    summary analytics.

    Args:
        hcp_id: Filter by HCP database ID.
        hcp_name: Filter by HCP name (partial match).
        interaction_type: Filter by type (call, email, visit, conference, virtual).
        sentiment: Filter by sentiment (positive, neutral, negative).
        product: Filter by product name discussed.
        topic: Filter by topic keyword.
        date_from: Start date filter in ISO format (YYYY-MM-DD).
        date_to: End date filter in ISO format (YYYY-MM-DD).
        limit: Maximum number of results to return (default 20).

    Returns:
        JSON string with matching interactions and summary analytics.
    """
    db: Session = get_db_session()
    try:
        query = db.query(Interaction)
        filters = []

        # Filter by HCP ID
        if hcp_id:
            filters.append(Interaction.hcp_id == hcp_id)

        # Filter by HCP name (requires join)
        if hcp_name:
            hcp = db.query(HCP).filter(HCP.name.ilike(f"%{hcp_name}%")).first()
            if hcp:
                filters.append(Interaction.hcp_id == hcp.id)
            else:
                return json.dumps({
                    "results": [],
                    "total": 0,
                    "message": f"No HCP found matching '{hcp_name}'.",
                })

        # Filter by interaction type
        if interaction_type:
            filters.append(Interaction.interaction_type == interaction_type)

        # Filter by sentiment
        if sentiment:
            filters.append(Interaction.sentiment == sentiment)

        # Filter by date range
        if date_from:
            try:
                dt_from = datetime.fromisoformat(date_from)
                filters.append(Interaction.date >= dt_from)
            except ValueError:
                return json.dumps({"error": f"Invalid date_from format: '{date_from}'"})

        if date_to:
            try:
                dt_to = datetime.fromisoformat(date_to)
                filters.append(Interaction.date <= dt_to)
            except ValueError:
                return json.dumps({"error": f"Invalid date_to format: '{date_to}'"})

        if filters:
            query = query.filter(and_(*filters))

        interactions = query.order_by(Interaction.date.desc()).all()

        # Post-query filtering for JSON fields (product, topic)
        if product:
            interactions = [
                i for i in interactions
                if product.lower() in [p.lower() for p in (i.products_discussed or [])]
            ]

        if topic:
            interactions = [
                i for i in interactions
                if any(topic.lower() in t.lower() for t in (i.key_topics or []))
            ]

        # Apply limit
        total_before_limit = len(interactions)
        interactions = interactions[:limit]

        # Build analytics summary
        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        type_counts: dict[str, int] = {}
        product_counts: dict[str, int] = {}
        topic_counts: dict[str, int] = {}

        for inter in interactions:
            sent = inter.sentiment or "neutral"
            sentiment_counts[sent] = sentiment_counts.get(sent, 0) + 1

            itype = inter.interaction_type or "unknown"
            type_counts[itype] = type_counts.get(itype, 0) + 1

            for p in (inter.products_discussed or []):
                product_counts[p] = product_counts.get(p, 0) + 1

            for t in (inter.key_topics or []):
                topic_counts[t] = topic_counts.get(t, 0) + 1

        # Resolve HCP names for display
        hcp_ids = list(set(i.hcp_id for i in interactions))
        hcps = db.query(HCP).filter(HCP.id.in_(hcp_ids)).all() if hcp_ids else []
        hcp_map = {h.id: h.name for h in hcps}

        serialized = []
        for inter in interactions:
            data = _serialize_interaction(inter)
            data["hcp_name"] = hcp_map.get(inter.hcp_id, "Unknown")
            serialized.append(data)

        result = {
            "results": serialized,
            "total": total_before_limit,
            "returned": len(serialized),
            "analytics": {
                "sentiment_breakdown": sentiment_counts,
                "type_breakdown": type_counts,
                "product_mentions": product_counts,
                "topic_frequency": topic_counts,
            },
        }

        return json.dumps(result, default=str)

    except Exception as e:
        return json.dumps({"error": f"Failed to search interactions: {str(e)}"})
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 5: suggest_next_action
# ---------------------------------------------------------------------------


@tool
def suggest_next_action(
    hcp_id: Optional[int] = None,
    hcp_name: Optional[str] = None,
) -> str:
    """Suggest the next best action for engaging an HCP.

    Analyses the HCP's interaction history, sentiment trends, product
    affinity, and engagement recency to recommend optimal next steps,
    visit timing, talking points, and content to share.

    Args:
        hcp_id: The database ID of the HCP.
        hcp_name: The name (or partial name) of the HCP (used if ID not provided).

    Returns:
        JSON string with recommended actions, timing, talking points,
        and content suggestions.
    """
    db: Session = get_db_session()
    try:
        hcp = None
        if hcp_id:
            hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
        elif hcp_name:
            hcp = db.query(HCP).filter(HCP.name.ilike(f"%{hcp_name}%")).first()

        if not hcp:
            search_term = hcp_id if hcp_id else hcp_name
            return json.dumps({"error": f"HCP not found for: {search_term}"})

        interactions = (
            db.query(Interaction)
            .filter(Interaction.hcp_id == hcp.id)
            .order_by(Interaction.date.desc())
            .all()
        )

        products = db.query(Product).filter(Product.status == "active").all()
        all_product_names = [p.name for p in products]

        engagement_score = _compute_engagement_score(interactions)

        # --- Analyse interaction history ---

        now = datetime.now(timezone.utc)

        # Days since last interaction
        days_since_last = None
        last_interaction = None
        if interactions:
            last_interaction = interactions[0]
            last_date = last_interaction.date
            if last_date:
                if last_date.tzinfo is None:
                    last_date = last_date.replace(tzinfo=timezone.utc)
                days_since_last = (now - last_date).days

        # Products already discussed
        discussed_products: set[str] = set()
        for inter in interactions:
            for p in (inter.products_discussed or []):
                discussed_products.add(p)

        # Products NOT yet discussed
        undiscussed_products = [p for p in all_product_names if p not in discussed_products]

        # Pending follow-ups
        pending_followups = [
            i for i in interactions
            if i.follow_up_required and i.follow_up_date and i.follow_up_date >= now - timedelta(days=7)
        ]

        # Overdue follow-ups
        overdue_followups = [
            i for i in interactions
            if i.follow_up_required and i.follow_up_date and i.follow_up_date < now - timedelta(days=1)
        ]

        # Most common interaction type
        type_counts: dict[str, int] = {}
        for inter in interactions:
            t = inter.interaction_type or "unknown"
            type_counts[t] = type_counts.get(t, 0) + 1
        preferred_channel = max(type_counts, key=type_counts.get) if type_counts else "call"

        # Sentiment trend
        recent_sentiments = [i.sentiment for i in interactions[:5] if i.sentiment]
        positive_ratio = recent_sentiments.count("positive") / len(recent_sentiments) if recent_sentiments else 0

        # --- Build recommendations ---

        recommendations = []
        talking_points = []
        content_suggestions = []

        # 1. Overdue follow-ups (highest priority)
        if overdue_followups:
            for fu in overdue_followups:
                recommendations.append({
                    "priority": "HIGH",
                    "action": f"Complete overdue follow-up from {fu.date.strftime('%Y-%m-%d') if fu.date else 'unknown date'}",
                    "details": fu.follow_up_notes or "No specific notes recorded.",
                    "channel": preferred_channel,
                })
            talking_points.append("Address outstanding action items from previous meetings.")

        # 2. Pending follow-ups
        if pending_followups and not overdue_followups:
            for fu in pending_followups:
                fu_date_str = fu.follow_up_date.strftime('%Y-%m-%d') if fu.follow_up_date else "soon"
                recommendations.append({
                    "priority": "MEDIUM",
                    "action": f"Scheduled follow-up by {fu_date_str}",
                    "details": fu.follow_up_notes or "Complete the planned follow-up.",
                    "channel": preferred_channel,
                })

        # 3. Re-engagement if no recent contact
        if days_since_last is not None and days_since_last > 30:
            recommendations.append({
                "priority": "HIGH",
                "action": f"Re-engage — last contact was {days_since_last} days ago",
                "details": f"Consider reaching out via {preferred_channel}. Relationship may be cooling.",
                "channel": preferred_channel,
            })
        elif days_since_last is not None and days_since_last > 14:
            recommendations.append({
                "priority": "MEDIUM",
                "action": f"Maintain cadence — last contact was {days_since_last} days ago",
                "details": f"A check-in {preferred_channel} would keep engagement strong.",
                "channel": preferred_channel,
            })

        # 4. Tier-based recommendations
        if hcp.tier == "KOL":
            recommendations.append({
                "priority": "MEDIUM",
                "action": "Consider advisory board or speaker engagement",
                "details": f"{hcp.name} is a KOL — explore thought leadership opportunities.",
                "channel": "visit",
            })
            talking_points.append("Invite to upcoming advisory board or speaker programme.")
            content_suggestions.append("Latest clinical data publications for peer review.")

        # 5. Product gap analysis
        if undiscussed_products:
            recommendations.append({
                "priority": "LOW",
                "action": f"Introduce undiscussed products: {', '.join(undiscussed_products[:3])}",
                "details": "These products have not been discussed with this HCP yet.",
                "channel": preferred_channel,
            })
            for prod_name in undiscussed_products[:2]:
                prod = next((p for p in products if p.name == prod_name), None)
                if prod and prod.key_messages:
                    talking_points.append(f"{prod_name}: {prod.key_messages[0]}")
                    content_suggestions.append(f"{prod_name} product brochure and clinical summary.")

        # 6. Talking points based on past topics
        all_topics: list[str] = []
        for inter in interactions[:5]:
            all_topics.extend(inter.key_topics or [])
        if all_topics:
            unique_topics = list(set(all_topics))[:5]
            talking_points.append(f"Continue discussion on: {', '.join(unique_topics)}")

        # 7. Content suggestions based on specialty
        specialty_content = {
            "Cardiology": ["Heart failure treatment guidelines update", "Cardiovascular outcomes trial data"],
            "Oncology": ["Latest NCCN guideline updates", "Immunotherapy combination data"],
            "Endocrinology": ["ADA Standards of Care update", "Weight management clinical evidence"],
            "Neurology": ["MS treatment algorithm updates", "Neuroimmunology research highlights"],
            "Rheumatology": ["ACR treatment recommendations", "Biologic therapy comparison data"],
            "Pulmonology": ["GOLD guidelines update", "Inhaler technique resources"],
            "Dermatology": ["AAD clinical guidelines", "Biologic treatment landscape review"],
            "Gastroenterology": ["AGA clinical practice updates", "IBD treatment advances"],
            "Hematology": ["ASH guideline updates", "CAR-T therapy real-world data"],
        }
        specialty_recs = specialty_content.get(hcp.specialty, [])
        content_suggestions.extend(specialty_recs)

        # 8. Optimal timing
        if hcp.tier in ("KOL", "High"):
            optimal_timing = "Within the next 7 days — high-value relationship requires regular touch points."
        elif days_since_last and days_since_last > 21:
            optimal_timing = "As soon as possible — engagement gap detected."
        else:
            optimal_timing = "Within the next 2-3 weeks at the HCP's convenience."

        # If no specific recommendations were generated
        if not recommendations:
            recommendations.append({
                "priority": "LOW",
                "action": "Maintain current engagement cadence",
                "details": "Relationship is healthy. Continue periodic check-ins.",
                "channel": preferred_channel,
            })

        result = {
            "hcp": {
                "id": hcp.id,
                "name": hcp.name,
                "specialty": hcp.specialty,
                "tier": hcp.tier,
                "institution": hcp.institution,
            },
            "engagement_score": engagement_score,
            "days_since_last_interaction": days_since_last,
            "total_interactions": len(interactions),
            "recommendations": recommendations,
            "optimal_timing": optimal_timing,
            "preferred_channel": preferred_channel,
            "talking_points": talking_points if talking_points else ["General check-in and relationship maintenance."],
            "content_suggestions": content_suggestions if content_suggestions else ["No specific content recommendations at this time."],
            "sentiment_trend": "Positive" if positive_ratio > 0.5 else ("Mixed" if positive_ratio > 0.2 else "Needs attention"),
        }

        return json.dumps(result, default=str)

    except Exception as e:
        return json.dumps({"error": f"Failed to suggest next action: {str(e)}"})
    finally:
        db.close()


# Expose the tool list for the graph and the API
ALL_TOOLS = [
    log_interaction,
    edit_interaction,
    get_hcp_profile,
    search_interactions,
    suggest_next_action,
]
