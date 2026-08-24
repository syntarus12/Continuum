"""Framework-neutral memory helpers.

Use these two functions from any agent runtime, including custom Python
loops, Hermes-style tool registries, OpenClaw/NemoClaw MCP bridges, or a
remote worker. The model provider is deliberately not coupled to memory.
"""

from __future__ import annotations

import os
from typing import Any

from syntarus import AsyncMemoryClient


def _client() -> AsyncMemoryClient:
    return AsyncMemoryClient(
        api_key=os.environ["SYNTARUS_API_KEY"],
        base_url=os.getenv("SYNTARUS_BASE_URL", "https://ai.syntarus.com/v1"),
    )


async def recall(query: str, *, user_id: str, agent_id: str | None = None, top_k: int = 8) -> str:
    """Return bounded context to place in a model prompt or tool result."""
    client = _client()
    try:
        result = await client.search(query, user_id=user_id, agent_id=agent_id, top_k=top_k)
        return result.get("context", "")
    finally:
        await client.aclose()


async def remember(
    user_message: str,
    assistant_message: str,
    *,
    user_id: str,
    agent_id: str | None = None,
    run_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Queue a completed turn for durable background extraction."""
    client = _client()
    try:
        accepted = await client.add(
            user_id=user_id,
            agent_id=agent_id,
            run_id=run_id,
            messages=[
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": assistant_message},
            ],
            metadata=metadata,
        )
        return await client.wait_for_event(accepted["event_id"])
    finally:
        await client.aclose()

