# Continuum Python SDK

The official Python client for the project-scoped Continuum memory API.

## Install

```bash
pip install syntarus
```

Python 3.10 or newer is required. Keep project API keys in a server-side
secret manager; never ship them in browser or mobile applications.

## Add and search memory

```python
from syntarus import MemoryClient

with MemoryClient(api_key="sk_mem_...") as memory:
    accepted = memory.add(
        user_id="customer_123",
        agent_id="support_agent",
        run_id="ticket_456",
        messages=[
            {"role": "user", "content": "I prefer vegetarian food."},
            {"role": "assistant", "content": "I will remember that."},
        ],
        metadata={"channel": "voice"},
        idempotency_key="call-456-final",
    )
    memory.wait_for_event(accepted["event_id"])
    result = memory.search(
        "What food does the customer prefer?",
        user_id="customer_123",
        agent_id="support_agent",
    )
    print(result["context"])
```

`agent_id` creates an isolated memory namespace. Omit it for a user profile
shared by every agent in the project. `run_id` groups the conversation history
used during ingestion. `metadata` is event metadata and is returned by event
status and webhook payloads; it is not currently a memory-search filter.

## Async client

```python
from syntarus import AsyncMemoryClient

async with AsyncMemoryClient(api_key="sk_mem_...") as memory:
    accepted = await memory.add(
        user_id="customer_123",
        messages=[{"role": "user", "content": "Call me after 5 PM."}],
    )
    await memory.wait_for_event(accepted["event_id"])
```

## Lifecycle operations

```python
memory.export(user_id="customer_123", agent_id="support_agent")
memory.delete("memory-uuid")
memory.delete_user(user_id="customer_123", agent_id="support_agent")
```

Deleting a user without `agent_id` deletes only the shared user namespace.
Delete each agent namespace separately when an application uses agent-scoped
memory.

## Enterprise isolation and governance

Use a project key with `tokens:write` to mint a short-lived credential for one
end user and, optionally, one agent. Subject tokens can only read or write
their bound namespace; they cannot export, delete, manage keys, or read audit
logs.

```python
issued = memory.create_subject_token(
    user_id="customer_123",
    agent_id="support_agent",
    scopes=["memories:read", "memories:write"],
    ttl_seconds=900,
)

with MemoryClient(api_key=issued["token"]) as delegated:
    delegated.search("What does this customer prefer?", user_id="customer_123")
```

Verified deletion is a durable cross-store job. Poll it with the normal event
method to receive the per-store completion receipt:

```python
deletion = memory.request_user_deletion(
    user_id="customer_123",
    agent_id="support_agent",
    idempotency_key="erase-customer-123-support",
)
receipt = memory.wait_for_event(deletion["event_id"])
print(receipt["result"]["stores"])

audit = memory.audit_events(user_id="customer_123", limit=50)
```

The project owner must enable delegated tokens in the developer console first.
Audit records intentionally exclude memory text and secret values.

## Webhooks

```python
created = memory.create_webhook("https://example.com/syntarus/events")
signing_secret = created["signing_secret"]  # returned once
memory.list_webhooks()
memory.webhook_deliveries(webhook_id=created["webhook"]["id"])
memory.delete_webhook(created["webhook"]["id"])
```

Deliveries include `X-Syntarus-Timestamp`, `X-Syntarus-Delivery`, and
`X-Syntarus-Signature-256`. Verify the signature as HMAC-SHA256 over
`<timestamp>.<raw_request_body>` and reject timestamps outside a five-minute
window. A non-2xx response is retried durably and eventually becomes a
dead-letter delivery visible through `webhook_deliveries`.

## Errors

The SDK raises typed exceptions derived from `SyntarusError`:

- `AuthenticationError`
- `PermissionDenied`
- `RateLimitError` (`retry_after` is available when the API sends it)
- `APIConnectionError`
- `APITimeoutError`
- `EventFailedError` (`event` contains the terminal event record)

## Continuum resources

- [Syntarus website](https://www.syntarus.com)
- [Developer portal](https://www.syntarus.com/pages/developers)
- [API reference](https://www.syntarus.com/pages/api-reference)
- [Security and reliability](https://www.syntarus.com/pages/security)
- [Source code](https://github.com/sujalkherawat25-stack/memoryos/tree/main/sdk)
- [Report an issue](https://github.com/sujalkherawat25-stack/memoryos/issues)
