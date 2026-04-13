"""
Legal Agent: RAG-powered legal Q&A grounded in Indian traffic law.
Uses LangGraph's checkpointed chat_messages for conversation memory.
"""
import json
import re
from typing import Dict, Any, List

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage

from app.config import settings
from app.rag.retriever import LegalRetriever
from app.rag.prompts import LEGAL_SYSTEM_PROMPT, LEGAL_QUERY_TEMPLATE, LANGUAGE_INSTRUCTION, LANGUAGE_NAMES, VEHICLE_TYPE_LABELS, resolve_language
from app.agents.state import TrafficJusticeState
from app.core.logging import get_logger

logger = get_logger(__name__)


def _strip_code_fences(text: str) -> str:
    """Strip markdown code fences (```json ... ```) from LLM output."""
    stripped = re.sub(r"^```(?:json)?\s*\n?", "", text.strip())
    stripped = re.sub(r"\n?```\s*$", "", stripped)
    return stripped.strip()


_VAGUE_PATTERNS = {
    "yes", "no", "ok", "haan", "nahi", "ha", "nah", "haa",
    "what to do", "kya karu", "kya kare", "help", "please",
    "solution", "aur", "then", "and", "but", "why",
}


def _is_vague_followup(query: str) -> bool:
    """Return True if the query is a vague follow-up that needs context enrichment."""
    words = query.lower().split()
    if len(words) > 8:
        return False
    if len(words) <= 3 and any(w in _VAGUE_PATTERNS for w in words):
        return True
    non_stop = [w for w in words if len(w) > 3]
    return len(non_stop) <= 1


def _build_retrieval_query(query: str, chat_history: List[BaseMessage]) -> str:
    """
    Build a context-aware retrieval query.
    Only enriches truly vague follow-ups ("ok", "what to do", "haan") with prior context.
    Messages describing a new event ("phone hiskavun ghetla", "mala maarla") are
    used as-is so the retriever finds documents matching the NEW situation.
    """
    if not _is_vague_followup(query):
        return query

    prior = chat_history[:-1] if chat_history else []
    if not prior:
        return query

    recent_human_msgs = [
        msg.content for msg in prior[-4:]
        if isinstance(msg, HumanMessage)
    ]
    if not recent_human_msgs:
        return query

    context_summary = " | ".join(recent_human_msgs[-2:])
    return f"{context_summary} — {query}"


def legal_agent_node(state: TrafficJusticeState) -> Dict[str, Any]:
    """LangGraph node for the Legal Agent."""
    query = state.get("query", "")
    user_state = state.get("state", "central")
    user_city = state.get("city") or "Not specified"
    raw_lang = state.get("language", "en") or "en"
    lang_explicit = state.get("language_explicit", False)
    lang_code = resolve_language(raw_lang, user_state, explicit=lang_explicit)
    language_name = LANGUAGE_NAMES.get(lang_code, "English")

    chat_history: list[BaseMessage] = list(state.get("chat_messages", []))

    retrieval_query = _build_retrieval_query(query, chat_history)
    logger.info(f"Retrieval query: {retrieval_query[:120]}...")

    retriever = LegalRetriever(top_k=10)
    retrieved_docs = retriever.retrieve(query=retrieval_query, state=user_state)

    context = "\n\n---\n\n".join(
        f"[Section {doc['metadata'].get('section', '?')} | "
        f"State: {doc['metadata'].get('state', 'central')} | "
        f"Topic: {doc['metadata'].get('topic', 'general')}]\n{doc['content']}"
        for doc in retrieved_docs
    )

    if not context.strip():
        context = "No relevant legal documents found in the corpus."

    lang_instruction = LANGUAGE_INSTRUCTION.format(language_name=language_name)

    raw_vehicle = state.get("vehicle_type") or ""
    vehicle_label = VEHICLE_TYPE_LABELS.get(raw_vehicle, "Not specified")

    last_bot_response = ""
    prior_msgs = chat_history[:-1] if chat_history else []
    for msg in reversed(prior_msgs):
        if isinstance(msg, AIMessage) and msg.content:
            last_bot_response = msg.content[:300]
            break

    prompt = LEGAL_QUERY_TEMPLATE.format(
        context=context,
        state=user_state,
        city=user_city,
        query=query,
        language_instruction=lang_instruction,
        last_response=last_bot_response,
        vehicle_type=vehicle_label,
    )

    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.1,
        api_key=settings.openai_api_key,
    )

    # Build LLM messages: system prompt + prior conversation (from checkpointer) + current RAG prompt
    llm_messages: list = [SystemMessage(content=LEGAL_SYSTEM_PROMPT)]

    # Include last 10 turns of history from checkpointer (excluding the current HumanMessage)
    prior = chat_history[:-1] if chat_history else []
    for msg in prior[-10:]:
        if isinstance(msg, HumanMessage):
            llm_messages.append(HumanMessage(content=msg.content))
        elif isinstance(msg, AIMessage):
            llm_messages.append(AIMessage(content=msg.content))

    llm_messages.append(HumanMessage(content=prompt))

    response = llm.invoke(llm_messages)

    raw_content = _strip_code_fences(response.content)

    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError:
        parsed = {
            "answer": response.content,
            "sections_cited": [],
            "fine_range": None,
            "recommended_action": "Please consult a legal professional.",
            "disclaimer": "This is informational only, not legal advice.",
        }

    logger.info(f"Legal agent processed query, cited {len(parsed.get('sections_cited', []))} sections")

    return {
        "legal_response": parsed,
        "response": parsed,
        "messages": [f"legal_agent: processed query about '{query[:50]}...'"],
    }
