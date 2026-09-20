# Coding-agent memory

Use the same two calls around a coding agent's tool loop: recall the relevant
project context before planning, then remember the final decision or verified
fix after the task completes.

Example:

    import os
    from syntarus import MemoryClient

    with MemoryClient(
        api_key=os.environ["SYNTARUS_API_KEY"],
        base_url=os.getenv("SYNTARUS_BASE_URL", "http://localhost:8000/v1"),
    ) as memory:
        context = memory.search(
            "previous decisions and failed fixes for the authentication flow",
            user_id="developer_42",
            agent_id="coding-agent",
        )

        # Give context["context"] to the coding model before it plans.
        print(context["context"])

        accepted = memory.add(
            user_id="developer_42",
            agent_id="coding-agent",
            run_id="pull-request-184",
            messages=[
                {"role": "user", "content": "The auth flow now validates callback state."},
                {"role": "assistant", "content": "Verified with the integration test suite."},
            ],
            idempotency_key="pull-request-184-auth-state",
        )
        memory.wait_for_event(accepted["event_id"])

Keep the API key in the coding agent's server-side environment. Do not place
it in a repository, editor extension bundle, or browser application.
