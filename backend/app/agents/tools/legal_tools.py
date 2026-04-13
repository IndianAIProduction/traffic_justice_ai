"""
Tools available to the Legal Agent for RAG retrieval.
Covers Motor Vehicles Act, CMVR, state rules, fine schedules, DL/RC rules,
insurance, road safety, commercial vehicles, e-challan procedures, and more.
"""
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool

from app.rag.retriever import LegalRetriever


@tool
def search_legal_corpus(
    query: str,
    state: Optional[str] = None,
    section: Optional[str] = None,
    topic: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Search the Indian traffic law corpus for relevant legal information.

    Args:
        query: The legal question or topic to search for.
        state: Indian state for state-specific rules (e.g., 'delhi', 'gujarat', 'west_bengal').
        section: Specific section number to filter by (e.g., '184', '185').
        topic: Topic filter — one of: mv_act, cmvr, penalties, driving_licence,
               registration, legal_remedies, insurance_claims, road_safety,
               commercial_vehicles, echallan_digital, fine_schedule, state_rules.
    """
    retriever = LegalRetriever(top_k=10)
    return retriever.retrieve(query=query, state=state, section=section, topic=topic)


@tool
def get_section_details(section_number: str, state: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get detailed information about a specific section of the Motor Vehicles Act,
    including state-specific fine amounts.

    Args:
        section_number: The section number (e.g., '184', '185', '194B').
        state: Optional state for state-specific penalty info.
    """
    retriever = LegalRetriever(top_k=5)
    return retriever.retrieve(
        query=f"Section {section_number} Motor Vehicles Act penalty fine",
        section=section_number,
        state=state,
    )


@tool
def search_state_rules(state: str, query: str) -> List[Dict[str, Any]]:
    """Search for state-specific RTO rules, fine rates, and procedures.

    Args:
        state: Indian state name (e.g., 'delhi', 'maharashtra', 'tamil_nadu').
        query: What to search for (e.g., 'road tax rates', 'helmet fine', 'e-challan').
    """
    retriever = LegalRetriever(top_k=8)
    return retriever.retrieve(query=f"{state} {query}", state=state)


@tool
def search_procedures(topic: str) -> List[Dict[str, Any]]:
    """Search for RTO procedures like DL application, RC transfer, NOC, insurance claim, etc.

    Args:
        topic: The procedure to search for (e.g., 'driving licence renewal',
               'vehicle transfer', 'insurance claim process', 'contest challan',
               'hit and run compensation', 'MACT claim').
    """
    retriever = LegalRetriever(top_k=8)
    return retriever.retrieve(query=topic)
