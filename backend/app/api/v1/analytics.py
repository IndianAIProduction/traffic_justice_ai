from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.audit import AnalyticsEvent
from app.models.challan import Challan
from app.models.complaint import Complaint
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/overcharges")
async def get_overcharge_patterns(
    state: str = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get anonymized overcharge patterns. No authentication required."""
    query = select(Challan).where(Challan.has_overcharge.is_(True))
    if state:
        query = query.join(Challan.case).where(
            Challan.case.has(state=state)
        )
    query = query.order_by(Challan.created_at.desc()).limit(limit)

    result = await db.execute(query)
    challans = result.scalars().all()

    patterns = []
    for c in challans:
        validation = c.validation_result or {}
        for analysis in validation.get("section_analysis", []):
            if analysis.get("is_overcharged"):
                patterns.append({
                    "section": analysis["section"],
                    "offense": analysis["offense"],
                    "charged": analysis["charged_amount"],
                    "valid_max": analysis.get("valid_range", {}).get("max"),
                    "overcharge": analysis["charged_amount"] - (
                        analysis.get("valid_range", {}).get("max", 0) or 0
                    ),
                })

    return {"patterns": patterns, "total": len(patterns)}


@router.get("/heatmap")
async def get_heatmap_data(
    state: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get geo-located incident data for heatmap visualization."""
    query = select(AnalyticsEvent).where(
        AnalyticsEvent.latitude.is_not(None),
        AnalyticsEvent.longitude.is_not(None),
    )
    if state:
        query = query.where(AnalyticsEvent.state == state)

    query = query.limit(1000)
    result = await db.execute(query)
    events = result.scalars().all()

    return {
        "points": [
            {
                "lat": e.latitude,
                "lng": e.longitude,
                "type": e.event_type,
                "city": e.city,
            }
            for e in events
        ]
    }


@router.get("/resolution-rates")
async def get_resolution_rates(
    state: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get complaint resolution rate statistics."""
    base = select(
        Complaint.status,
        func.count(Complaint.id).label("count"),
    ).group_by(Complaint.status)

    result = await db.execute(base)
    rows = result.all()

    status_counts = {row[0].value if hasattr(row[0], 'value') else row[0]: row[1] for row in rows}
    total = sum(status_counts.values())

    return {
        "total_complaints": total,
        "by_status": status_counts,
        "resolution_rate": (
            round(status_counts.get("resolved", 0) / total * 100, 1)
            if total > 0 else 0
        ),
    }


@router.get("/state/{state_code}")
async def get_state_stats(
    state_code: str,
    db: AsyncSession = Depends(get_db),
):
    """Get statistics for a specific state."""
    challan_count = await db.execute(
        select(func.count(Challan.id)).join(Challan.case).where(
            Challan.case.has(state=state_code)
        )
    )
    overcharge_count = await db.execute(
        select(func.count(Challan.id))
        .join(Challan.case)
        .where(Challan.case.has(state=state_code), Challan.has_overcharge.is_(True))
    )

    total = challan_count.scalar() or 0
    overcharged = overcharge_count.scalar() or 0

    return {
        "state": state_code,
        "total_challans_validated": total,
        "overcharges_detected": overcharged,
        "overcharge_rate": round(overcharged / total * 100, 1) if total > 0 else 0,
    }
