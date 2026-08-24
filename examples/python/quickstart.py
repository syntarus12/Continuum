"""Small, provider-neutral Community Edition smoke example."""

from __future__ import annotations

import os

from syntarus import MemoryClient


def main() -> None:
    api_key = os.getenv("SYNTARUS_API_KEY", "sk_mem_community")
    base_url = os.getenv("SYNTARUS_BASE_URL", "http://localhost:8000/v1")
    user_id = os.getenv("SYNTARUS_USER_ID", "demo-user")
    agent_id = os.getenv("SYNTARUS_AGENT_ID", "demo-agent")

    with MemoryClient(api_key=api_key, base_url=base_url) as memory:
        accepted = memory.add(
            user_id=user_id,
            agent_id=agent_id,
            run_id="community-quickstart",
            messages=[
                {"role": "user", "content": "I prefer concise status updates."},
                {"role": "assistant", "content": "I will keep updates concise."},
            ],
            idempotency_key="community-quickstart-1",
        )
        print("Accepted event:", accepted.get("event_id"))
        event = memory.wait_for_event(accepted["event_id"], timeout=90)
        print("Ingestion:", event.get("status"))

        result = memory.search(
            "How should I receive status updates?",
            user_id=user_id,
            agent_id=agent_id,
            top_k=5,
        )
        print("Retrieved context:\n", result.get("context", "(no context)"))


if __name__ == "__main__":
    main()

