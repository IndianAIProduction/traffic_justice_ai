"""
Evidence service: handles transcription, analysis, and misconduct detection.
"""
import os

from openai import OpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.evidence import Evidence, MisconductFlag
from app.core.security import decrypt_data
from app.agents.orchestrator import run_orchestrator
from app.core.logging import get_logger

logger = get_logger(__name__)


async def transcribe_evidence(evidence: Evidence, db: AsyncSession) -> Evidence:
    """Transcribe audio/video evidence using OpenAI Whisper."""
    full_path = os.path.join(settings.evidence_storage_path, evidence.file_path)

    if not os.path.exists(full_path):
        logger.error(f"Evidence file not found: {full_path}")
        return evidence

    try:
        with open(full_path, "rb") as f:
            encrypted_content = f.read()
        decrypted_content = decrypt_data(encrypted_content)

        temp_path = f"/tmp/evidence_{evidence.id}"
        with open(temp_path, "wb") as f:
            f.write(decrypted_content)

        client = OpenAI(api_key=settings.openai_api_key)
        with open(temp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",
            )

        evidence.transcription = transcript
        await db.flush()

        os.remove(temp_path)
        logger.info(f"Transcribed evidence {evidence.id}: {len(transcript)} chars")

    except Exception as e:
        logger.error(f"Transcription failed for evidence {evidence.id}: {e}")

    return evidence


async def analyze_evidence_transcription(evidence: Evidence, db: AsyncSession) -> Evidence:
    """Analyze evidence transcription for misconduct using the Evidence Agent."""
    if not evidence.transcription:
        return evidence

    result = await run_orchestrator(
        query="Analyze this evidence transcription for misconduct",
        user_id="system",
        intent="evidence_analysis",
        transcription=evidence.transcription,
    )

    response = result.get("response", {})
    evidence.analysis = response
    evidence.is_analyzed = True

    flags = response.get("misconduct_flags", [])
    for flag_data in flags:
        flag = MisconductFlag(
            evidence_id=evidence.id,
            flag_type=flag_data.get("flag_type", "unknown"),
            severity=flag_data.get("severity", 1),
            description=flag_data.get("description", ""),
            timestamp_in_media=flag_data.get("timestamp"),
            confidence_score=flag_data.get("confidence"),
            raw_quote=flag_data.get("raw_quote"),
        )
        db.add(flag)

    await db.flush()
    await db.refresh(evidence)

    logger.info(
        f"Analyzed evidence {evidence.id}: "
        f"{len(flags)} misconduct flags detected"
    )

    return evidence
