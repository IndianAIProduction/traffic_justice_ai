from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.case import Case, CaseType, CaseStatus
from app.schemas.case import CaseCreateRequest, CaseUpdateRequest, CaseResponse, CaseDetailResponse
from app.core.exceptions import NotFoundException

router = APIRouter()


@router.post("", response_model=CaseResponse, status_code=201)
async def create_case(
    data: CaseCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new case."""
    case = Case(
        user_id=current_user.id,
        case_type=CaseType(data.case_type),
        status=CaseStatus.OPEN,
        title=data.title,
        description=data.description,
        state=data.state,
        city=data.city,
        location=data.location,
    )
    db.add(case)
    await db.flush()
    await db.refresh(case)
    return CaseResponse.model_validate(case)


@router.get("", response_model=List[CaseResponse])
async def list_cases(
    status: str = Query(None),
    case_type: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List current user's cases with optional filters."""
    query = select(Case).where(Case.user_id == current_user.id)

    if status:
        query = query.where(Case.status == CaseStatus(status))
    if case_type:
        query = query.where(Case.case_type == CaseType(case_type))

    query = query.order_by(Case.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return [CaseResponse.model_validate(c) for c in result.scalars().all()]


@router.get("/{case_id}", response_model=CaseDetailResponse)
async def get_case(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed case information with related entities."""
    result = await db.execute(
        select(Case).where(Case.id == case_id, Case.user_id == current_user.id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise NotFoundException("Case")
    return CaseDetailResponse.model_validate(case)


@router.patch("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: uuid.UUID,
    data: CaseUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update case details."""
    result = await db.execute(
        select(Case).where(Case.id == case_id, Case.user_id == current_user.id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise NotFoundException("Case")

    update_data = data.model_dump(exclude_unset=True)
    if "status" in update_data:
        update_data["status"] = CaseStatus(update_data["status"])

    for key, value in update_data.items():
        setattr(case, key, value)

    await db.flush()
    await db.refresh(case)
    return CaseResponse.model_validate(case)
