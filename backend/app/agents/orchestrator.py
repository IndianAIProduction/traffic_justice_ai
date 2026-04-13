"""
LangGraph Orchestrator: Classifies user intent and routes to specialized agents.
Uses LangGraph MemorySaver for thread-based conversation memory.
"""
import json
import uuid
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.config import settings
from app.agents.state import TrafficJusticeState
from app.agents.legal_agent import legal_agent_node
from app.agents.challan_agent import challan_agent_node
from app.agents.evidence_agent import evidence_agent_node
from app.agents.complaint_agent import complaint_agent_node
from app.agents.portal_agent import portal_agent_node
from app.agents.tracker_agent import tracker_agent_node
from app.core.logging import get_logger

logger = get_logger(__name__)

VALID_INTENTS = [
    "legal_query",
    "challan_validation",
    "evidence_analysis",
    "complaint_draft",
    "portal_submit",
    "status_check",
]

checkpointer = MemorySaver()


def classify_intent(state: TrafficJusticeState) -> Dict[str, Any]:
    """Classify user intent to route to the appropriate agent."""
    if state.get("intent") and state["intent"] in VALID_INTENTS:
        return {"messages": [f"orchestrator: using provided intent '{state['intent']}'"]}

    query = state.get("query", "")

    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        api_key=settings.openai_api_key,
    )

    response = llm.invoke([
        SystemMessage(content=(
            "You are an intent classifier for a traffic justice platform. "
            "Classify the user's message into exactly one of these categories:\n"
            "- legal_query: Questions about traffic law, rights, fines, procedures\n"
            "- challan_validation: Wants to validate a challan/fine amount\n"
            "- evidence_analysis: Wants to analyze audio/video evidence\n"
            "- complaint_draft: Wants to draft or create a complaint\n"
            "- portal_submit: Wants to submit a complaint to a portal\n"
            "- status_check: Wants to check complaint status\n\n"
            "Respond with ONLY the category name, nothing else."
        )),
        HumanMessage(content=query),
    ])

    intent = response.content.strip().lower().replace(" ", "_")
    if intent not in VALID_INTENTS:
        intent = "legal_query"

    logger.info(f"Orchestrator classified intent: {intent}")

    return {
        "intent": intent,
        "messages": [f"orchestrator: classified intent as '{intent}'"],
    }


def route_by_intent(state: TrafficJusticeState) -> str:
    """Route to the appropriate agent based on classified intent."""
    intent = state.get("intent", "legal_query")
    route_map = {
        "legal_query": "legal_agent",
        "challan_validation": "challan_agent",
        "evidence_analysis": "evidence_agent",
        "complaint_draft": "complaint_agent",
        "portal_submit": "portal_agent",
        "status_check": "tracker_agent",
    }
    return route_map.get(intent, "legal_agent")


def format_response(state: TrafficJusticeState) -> Dict[str, Any]:
    """Format the final response with metadata and disclaimer."""
    response = state.get("response", {})

    if isinstance(response, dict) and "disclaimer" not in response:
        response["disclaimer"] = (
            "This information is provided by Traffic Justice AI for educational "
            "purposes only. It does not constitute legal advice. Please consult "
            "a qualified legal professional for specific legal matters."
        )

    answer_text = ""
    if isinstance(response, dict):
        answer_text = response.get("answer", json.dumps(response))
    else:
        answer_text = str(response)

    return {
        "response": response,
        "chat_messages": [AIMessage(content=answer_text)],
        "messages": ["orchestrator: formatted final response"],
    }


def build_orchestrator_graph() -> StateGraph:
    """Build the LangGraph orchestrator (uncompiled)."""
    graph = StateGraph(TrafficJusticeState)

    graph.add_node("classifier", classify_intent)
    graph.add_node("legal_agent", legal_agent_node)
    graph.add_node("challan_agent", challan_agent_node)
    graph.add_node("evidence_agent", evidence_agent_node)
    graph.add_node("complaint_agent", complaint_agent_node)
    graph.add_node("portal_agent", portal_agent_node)
    graph.add_node("tracker_agent", tracker_agent_node)
    graph.add_node("formatter", format_response)

    graph.set_entry_point("classifier")

    graph.add_conditional_edges(
        "classifier",
        route_by_intent,
        {
            "legal_agent": "legal_agent",
            "challan_agent": "challan_agent",
            "evidence_agent": "evidence_agent",
            "complaint_agent": "complaint_agent",
            "portal_agent": "portal_agent",
            "tracker_agent": "tracker_agent",
        },
    )

    for agent in [
        "legal_agent", "challan_agent", "evidence_agent",
        "complaint_agent", "portal_agent", "tracker_agent",
    ]:
        graph.add_edge(agent, "formatter")

    graph.add_edge("formatter", END)

    return graph


_graph_builder = build_orchestrator_graph()


async def run_orchestrator(
    query: str,
    user_id: str,
    state: str = "central",
    city: str = None,
    intent: str = None,
    thread_id: str = None,
    language: str = "en",
    vehicle_type: str = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Run the orchestrator with LangGraph checkpointer-based memory.
    The checkpointer automatically persists chat_messages per thread_id,
    so follow-up queries in the same thread have full conversation context.
    """
    graph = _graph_builder.compile(checkpointer=checkpointer)

    input_state: dict = {
        "query": query,
        "user_id": user_id,
        "state": state,
        "city": city,
        "language": language,
        "language_explicit": kwargs.pop("language_explicit", False),
        "vehicle_type": vehicle_type,
        "chat_messages": [HumanMessage(content=query)],
        "messages": [],
    }

    if intent:
        input_state["intent"] = intent

    input_state.update(kwargs)

    config = {"configurable": {"thread_id": thread_id or str(uuid.uuid4())}}

    result = await graph.ainvoke(input_state, config)

    return {
        "response": result.get("response", {}),
        "intent": result.get("intent", "unknown"),
        "audit_trail": result.get("messages", []),
        "thread_id": config["configurable"]["thread_id"],
    }
