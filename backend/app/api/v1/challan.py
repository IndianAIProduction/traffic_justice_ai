from typing import List, Dict
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.case import Case
from app.models.challan import Challan
from app.schemas.challan import ChallanValidateRequest, ChallanResponse, ScheduleSectionItem
from app.services.challan_service import (
    create_and_validate_challan,
    get_available_states,
    get_schedule_sections,
)
from app.core.exceptions import NotFoundException, ForbiddenException

router = APIRouter()


@router.get("/states", response_model=List[Dict])
async def list_supported_states():
    """List all Indian states/UTs with available traffic fine schedules."""
    return get_available_states()


@router.get("/schedule-sections", response_model=List[ScheduleSectionItem])
async def list_schedule_sections(
    state: str = Query(..., description="State or UT name (e.g. Maharashtra, Delhi)"),
):
    """All MV Act section codes in our fine schedule for this state (for challan entry UI)."""
    return get_schedule_sections(state)


@router.post("/validate", response_model=ChallanResponse, status_code=201)
async def validate_challan(
    data: ChallanValidateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Validate a traffic challan against official fine schedules."""
    if data.case_id:
        result = await db.execute(select(Case).where(Case.id == data.case_id))
        case = result.scalar_one_or_none()
        if not case:
            raise NotFoundException("Case")
        if case.user_id != current_user.id:
            raise ForbiddenException("You do not own this case")

    challan = await create_and_validate_challan(data, current_user.id, db)
    return challan


@router.get("/{challan_id}", response_model=ChallanResponse)
async def get_challan(
    challan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get challan details and validation result."""
    result = await db.execute(
        select(Challan)
        .join(Challan.case)
        .where(Challan.id == challan_id, Case.user_id == current_user.id)
    )
    challan = result.scalar_one_or_none()
    if not challan:
        raise NotFoundException("Challan")
    return challan
