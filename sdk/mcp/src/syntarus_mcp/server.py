"""Local stdio MCP server. Deliberately exposes no delete or export tools."""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP
from syntarus import AsyncMemoryClient

mcp = FastMCP("Continuum Memory")


def _client() -> AsyncMemoryClient:
    api_key = os.environ.get("SYNTARUS_API_KEY", "")
    if not api_key:
        raise RuntimeError("SYNTARUS_API_KEY is required. Keep it in your environment, not this MCP config.")
    return AsyncMemoryClient(api_key)


def _user_id(user_id: str | None) -> str:
    """Use an explicit target when supplied, otherwise this Codex identity."""
    resolved = user_id or os.environ.get("SYNTARUS_USER_ID", "")
    if not resolved:
        raise RuntimeError("Set SYNTARUS_USER_ID once, or supply user_id for this call.")
    return resolved


@mcp.tool()
async def search_memory(query: str, user_id: str | None = None, limit: int = 10) -> dict:
    """Retrieve memories for the default Codex user or an explicitly supplied user."""
    if not 1 <= limit <= 50:
        raise ValueError("limit must be between 1 and 50")
    client = _client()
    try:
        return await client.search(query, user_id=_user_id(user_id), top_k=limit)
    finally:
        await client.aclose()


@mcp.tool()
async def remember(content: str, user_id: str | None = None, idempotency_key: str | None = None) -> dict:
    """Save explicitly supplied information for the default or an explicit user."""
    client = _client()
    try:
        return await client.add(
            user_id=_user_id(user_id),
            messages=[{"role": "user", "content": content}],
            idempotency_key=idempotency_key,
        )
    finally:
        await client.aclose()


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
