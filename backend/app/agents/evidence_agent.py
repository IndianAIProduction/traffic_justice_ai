"""
Evidence Agent: Analyzes transcriptions for misconduct, abuse, and timeline extraction.
"""
import json
import re
from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.rag.prompts import EVIDENCE_ANALYSIS_PROMPT
from app.agents.state import TrafficJusticeState
from app.core.logging import get_logger

logger = get_logger(__name__)


def _strip_code_fences(text: str) -> str:
    stripped = re.sub(r"^```(?:json)?\s*\n?", "", text.strip())
    stripped = re.sub(r"\n?```\s*$", "", stripped)
    return stripped.strip()


def evidence_agent_node(state: TrafficJusticeState) -> Dict[str, Any]:
    """LangGraph node for the Evidence Agent."""
    transcription = state.get("transcription", "")

    if not transcription:
        return {
            "evidence_analysis": {"error": "No transcription provided"},
            "response": {"error": "No transcription available for analysis"},
            "messages": ["evidence_agent: no transcription provided"],
        }

    prompt = EVIDENCE_ANALYSIS_PROMPT.format(transcription=transcription)

    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.1,
        api_key=settings.openai_api_key,
    )

    response = llm.invoke([
        SystemMessage(content=(
            "You are an evidence analysis agent for the Traffic Justice AI platform. "
            "Analyze traffic stop recordings objectively and factually. "
            "Only flag misconduct when there is clear evidence. "
            "Be conservative with severity scores."
        )),
        HumanMessage(content=prompt),
    ])

    try:
        parsed = json.loads(_strip_code_fences(response.content))
    except json.JSONDecodeError:
        parsed = {
            "misconduct_detected": False,
            "misconduct_flags": [],
            "timeline": [],
            "overall_severity": 0,
            "summary": response.content,
        }

    flag_count = len(parsed.get("misconduct_flags", []))
    logger.info(f"Evidence agent analyzed transcription, found {flag_count} flags")

    return {
        "evidence_analysis": parsed,
        "response": parsed,
        "messages": [f"evidence_agent: analyzed transcription, {flag_count} misconduct flags"],
    }
