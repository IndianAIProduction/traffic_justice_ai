"""
Complaint Agent: Drafts structured legal complaints for grievance portals.
"""
import json
import re
from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.rag.prompts import COMPLAINT_DRAFT_PROMPT, LANGUAGE_NAMES
from app.agents.state import TrafficJusticeState
from app.core.logging import get_logger

logger = get_logger(__name__)


def _strip_code_fences(text: str) -> str:
    stripped = re.sub(r"^```(?:json)?\s*\n?", "", text.strip())
    stripped = re.sub(r"\n?```\s*$", "", stripped)
    return stripped.strip()


def complaint_agent_node(state: TrafficJusticeState) -> Dict[str, Any]:
    """LangGraph node for the Complaint Agent."""
    case_details = state.get("case_details", "No case details provided")
    evidence_summary = state.get("evidence_summary", "No evidence summary available")
    lang_code = state.get("language", "en") or "en"
    language_name = LANGUAGE_NAMES.get(lang_code, "English")

    legal_sections = []
    if state.get("legal_response"):
        legal_sections = state["legal_response"].get("sections_cited", [])
    if state.get("evidence_analysis"):
        flags = state["evidence_analysis"].get("misconduct_flags", [])
        for flag in flags:
            legal_sections.append(f"Misconduct: {flag.get('flag_type', 'unknown')}")

    prompt = COMPLAINT_DRAFT_PROMPT.format(
        case_details=case_details,
        evidence_summary=evidence_summary,
        legal_sections="\n".join(legal_sections) if legal_sections else "None identified",
    )

    lang_sys = ""
    if lang_code != "en":
        lang_sys = f" Draft the complaint body in {language_name} using native script. Keep legal citations, section numbers, and formal headers in English."

    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.2,
        api_key=settings.openai_api_key,
    )

    response = llm.invoke([
        SystemMessage(content=(
            "You are a complaint drafting agent. Draft professional, factual, "
            "legally grounded complaints. Never fabricate evidence or exaggerate. "
            "The complaint must be suitable for submission to Indian grievance portals."
            + lang_sys
        )),
        HumanMessage(content=prompt),
    ])

    try:
        parsed = json.loads(_strip_code_fences(response.content))
    except json.JSONDecodeError:
        parsed = {
            "recipient": "Traffic Police Authority",
            "subject": "Grievance Complaint",
            "body": response.content,
            "evidence_list": [],
            "legal_citations": legal_sections,
            "relief_sought": "Investigation and appropriate action",
        }

    logger.info("Complaint agent drafted complaint")

    return {
        "complaint_draft": parsed,
        "response": parsed,
        "messages": ["complaint_agent: drafted complaint"],
    }
