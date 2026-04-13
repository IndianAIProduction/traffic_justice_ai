from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.legal_query import LegalQuery
from app.schemas.legal import LegalQueryRequest, LegalQueryResponse
from app.agents.orchestrator import run_orchestrator

router = APIRouter()


@router.post("/query", response_model=LegalQueryResponse)
async def legal_query(
    data: LegalQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ask a legal question about Indian traffic law."""
    result = await run_orchestrator(
        query=data.query,
        user_id=str(current_user.id),
        state=data.state,
        city=data.city,
        intent="legal_query",
        thread_id=data.thread_id,
        language=data.language,
        language_explicit=data.language_explicit,
        vehicle_type=data.vehicle_type,
    )

    record = LegalQuery(
        user_id=current_user.id,
        case_id=data.case_id,
        query_text=data.query,
        response_text=str(result.get("response", {})),
        sections_cited=result.get("response", {}).get("sections_cited", []),
        state=data.state,
        extra_metadata={"audit_trail": result.get("audit_trail", [])},
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)

    return LegalQueryResponse(
        id=record.id,
        query=data.query,
        response=result.get("response", {}),
        intent=result.get("intent", "legal_query"),
        audit_trail=result.get("audit_trail", []),
        thread_id=result.get("thread_id", ""),
    )
