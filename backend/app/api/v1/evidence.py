import hashlib
import os
import uuid
from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.case import Case
from app.models.evidence import Evidence, FileType
from app.schemas.evidence import EvidenceUploadResponse, EvidenceDetailResponse
from app.core.exceptions import NotFoundException, ValidationException, ForbiddenException
from app.core.security import encrypt_data
from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

MIME_TYPE_MAP = {
    "audio/mpeg": FileType.AUDIO,
    "audio/wav": FileType.AUDIO,
    "audio/ogg": FileType.AUDIO,
    "audio/mp4": FileType.AUDIO,
    "video/mp4": FileType.VIDEO,
    "video/webm": FileType.VIDEO,
    "video/quicktime": FileType.VIDEO,
    "image/jpeg": FileType.IMAGE,
    "image/png": FileType.IMAGE,
    "application/pdf": FileType.DOCUMENT,
}

MAX_SIZE = settings.max_upload_size_mb * 1024 * 1024


@router.post("/upload", response_model=EvidenceUploadResponse, status_code=201)
async def upload_evidence(
    file: UploadFile = File(...),
    case_id: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload evidence file (audio, video, image, or document)."""
    case_id = case_id.strip()

    if case_id:
        try:
            case_uuid = uuid.UUID(case_id)
        except ValueError:
            raise ValidationException(
                "Invalid Case ID format. Use a valid UUID from your Cases page, or leave blank to auto-create."
            )
        case_result = await db.execute(select(Case).where(Case.id == case_uuid))
        case = case_result.scalar_one_or_none()
        if not case:
            raise NotFoundException("Case")
        if case.user_id != current_user.id:
            raise ForbiddenException("You do not own this case")
    else:
        from app.models.case import CaseType, CaseStatus
        case = Case(
            user_id=current_user.id,
            case_type=CaseType.MISCONDUCT,
            status=CaseStatus.OPEN,
            title=f"Evidence: {file.filename or 'Upload'}",
        )
        db.add(case)
        await db.flush()

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise ValidationException(f"File exceeds maximum size of {settings.max_upload_size_mb}MB")

    content_type = file.content_type or "application/octet-stream"
    file_type = MIME_TYPE_MAP.get(content_type)
    if not file_type:
        raise ValidationException(f"Unsupported file type: {content_type}")

    file_hash = hashlib.sha256(content).hexdigest()

    evidence_id = uuid.uuid4()
    relative_path = f"{case.id}/{evidence_id}_{file.filename}"
    full_path = os.path.join(settings.evidence_storage_path, relative_path)

    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    try:
        encrypted_content = encrypt_data(content)
        with open(full_path, "wb") as f:
            f.write(encrypted_content)
    except Exception as e:
        logger.error(f"Failed to store evidence file: {e}")
        raise ValidationException("Failed to store evidence file")

    evidence = Evidence(
        id=evidence_id,
        case_id=case.id,
        file_type=file_type,
        file_path=relative_path,
        file_name=file.filename,
        file_hash=file_hash,
        file_size_bytes=len(content),
        mime_type=content_type,
    )
    db.add(evidence)
    await db.flush()
    await db.refresh(evidence)

    return EvidenceUploadResponse.model_validate(evidence)


@router.get("/{evidence_id}", response_model=EvidenceDetailResponse)
async def get_evidence(
    evidence_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get evidence details with analysis results."""
    result = await db.execute(
        select(Evidence)
        .join(Evidence.case)
        .where(Evidence.id == evidence_id, Case.user_id == current_user.id)
    )
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise NotFoundException("Evidence")
    return EvidenceDetailResponse.model_validate(evidence)


@router.post("/{evidence_id}/analyze", response_model=EvidenceDetailResponse)
async def analyze_evidence(
    evidence_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger analysis of uploaded evidence."""
    result = await db.execute(
        select(Evidence)
        .join(Evidence.case)
        .where(Evidence.id == evidence_id, Case.user_id == current_user.id)
    )
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise NotFoundException("Evidence")

    if evidence.file_type in (FileType.AUDIO, FileType.VIDEO) and not evidence.transcription:
        from app.services.evidence_service import transcribe_evidence
        evidence = await transcribe_evidence(evidence, db)

    if evidence.transcription and not evidence.is_analyzed:
        from app.services.evidence_service import analyze_evidence_transcription
        evidence = await analyze_evidence_transcription(evidence, db)

    return EvidenceDetailResponse.model_validate(evidence)


@router.get("/case/{case_id}", response_model=List[EvidenceUploadResponse])
async def list_case_evidence(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all evidence for a case."""
    case_result = await db.execute(select(Case).where(Case.id == case_id))
    case = case_result.scalar_one_or_none()
    if not case:
        raise NotFoundException("Case")
    if case.user_id != current_user.id:
        raise ForbiddenException("You do not own this case")

    result = await db.execute(
        select(Evidence)
        .where(Evidence.case_id == case_id)
        .order_by(Evidence.uploaded_at.desc())
    )
    return [EvidenceUploadResponse.model_validate(e) for e in result.scalars().all()]
