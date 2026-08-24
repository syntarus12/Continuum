"""LangGraph nodes for a bounded recall/remember lane."""

from __future__ import annotations

from typing import Any

from .generic import recall, remember


async def recall_node(state: dict[str, Any]) -> dict[str, Any]:
    query = str(state.get("input", state.get("messages", "")))
    context = await recall(query, user_id=state["user_id"], agent_id=state.get("agent_id", "langgraph"))
    return {"memory_context": context}


async def remember_node(state: dict[str, Any]) -> dict[str, Any]:
    await remember(
        str(state.get("input", "")),
        str(state.get("answer", "")),
        user_id=state["user_id"],
        agent_id=state.get("agent_id", "langgraph"),
        run_id=state.get("run_id"),
    )
    return {"memory_saved": True}

