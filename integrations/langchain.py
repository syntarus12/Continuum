"""LangChain recipe: recall before invoke, remember after invoke.

Install the optional framework separately. This adapter does not replace the
LLM or LangChain's tools; it only provides durable cross-session memory.
"""

from __future__ import annotations

from typing import Any

from .generic import recall, remember


class SyntarusLangChainMemory:
    def __init__(self, *, user_id: str, agent_id: str = "langchain"):
        self.user_id = user_id
        self.agent_id = agent_id

    async def load_memory_variables(self, inputs: dict[str, Any]) -> dict[str, str]:
        query = str(inputs.get("input", inputs.get("question", "")))
        return {"syntarus_memory": await recall(query, user_id=self.user_id, agent_id=self.agent_id)}

    async def save_context(self, inputs: dict[str, Any], outputs: dict[str, Any]) -> None:
        await remember(
            str(inputs.get("input", "")),
            str(outputs.get("output", outputs)),
            user_id=self.user_id,
            agent_id=self.agent_id,
        )

