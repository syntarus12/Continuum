"""Synchronous and asynchronous clients for the Syntarus v1 memory API."""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

import httpx

from .exceptions import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    EventFailedError,
    PermissionDenied,
    RateLimitError,
    SyntarusError,
)

DEFAULT_BASE_URL = "https://ai.syntarus.com/v1"


def _raise_for_response(response: httpx.Response) -> None:
    if response.is_success:
        return
    try:
        detail = response.json().get("detail", "Request failed.")
    except Exception:
        detail = "Request failed."
    if response.status_code == 401:
        raise AuthenticationError("Project API key was rejected.")
    if response.status_code == 403:
        raise PermissionDenied(str(detail))
    if response.status_code == 429:
        raw_retry = response.headers.get("Retry-After")
        try:
            retry_after = float(raw_retry) if raw_retry is not None else None
        except ValueError:
            retry_after = None
        raise RateLimitError("Project API rate limit exceeded.", retry_after=retry_after)
    raise SyntarusError(f"Syntarus API error ({response.status_code}): {detail}")


class _BaseClient:
    def __init__(self, api_key: str, *, base_url: str = DEFAULT_BASE_URL, timeout: float = 20.0):
        if not api_key.startswith(("sk_mem_", "st_mem_")):
            raise ValueError("api_key must be a Syntarus project key or subject token")
        self._base_url = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {api_key}", "User-Agent": "syntarus-python/0.2.0"}
        self._timeout = timeout

    @staticmethod
    def _payload(user_id: str, messages: list[dict[str, str]], agent_id: str | None, run_id: str | None, metadata: dict[str, Any] | None) -> dict[str, Any]:
        return {"user_id": user_id, "messages": messages, "agent_id": agent_id, "run_id": run_id, "metadata": metadata or {}}


class MemoryClient(_BaseClient):
    """Blocking client. Use ``AsyncMemoryClient`` inside async applications."""

    def __init__(self, api_key: str, *, base_url: str = DEFAULT_BASE_URL, timeout: float = 20.0):
        super().__init__(api_key, base_url=base_url, timeout=timeout)
        self._client = httpx.Client(base_url=self._base_url, headers=self._headers, timeout=self._timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "MemoryClient":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.TimeoutException as exc:
            raise APITimeoutError("Syntarus API request timed out.") from exc
        except httpx.RequestError as exc:
            raise APIConnectionError("Could not connect to the Syntarus API.") from exc
        _raise_for_response(response)
        return response

    def add(self, *, user_id: str, messages: list[dict[str, str]], agent_id: str | None = None, run_id: str | None = None, metadata: dict[str, Any] | None = None, idempotency_key: str | None = None) -> dict[str, Any]:
        response = self._request("POST", "/memories", json=self._payload(user_id, messages, agent_id, run_id, metadata), headers={"Idempotency-Key": idempotency_key or uuid.uuid4().hex})
        return response.json()

    def event(self, event_id: str) -> dict[str, Any]:
        response = self._request("GET", f"/events/{event_id}")
        return response.json()

    def wait_for_event(self, event_id: str, *, timeout: float = 60.0, poll_interval: float = 0.5) -> dict[str, Any]:
        if timeout <= 0 or poll_interval <= 0:
            raise ValueError("timeout and poll_interval must be positive")
        deadline = time.monotonic() + timeout
        while True:
            event = self.event(event_id)
            if event.get("status") == "succeeded":
                return event
            if event.get("status") in {"dead_letter", "cancelled"}:
                raise EventFailedError(event)
            if time.monotonic() >= deadline:
                raise APITimeoutError(f"Timed out waiting for event {event_id}.")
            time.sleep(min(poll_interval, max(0.0, deadline - time.monotonic())))

    def search(self, query: str, *, user_id: str, top_k: int = 10, agent_id: str | None = None, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        """Search with optional provenance filters (enforced by API v1.1+)."""
        response = self._request("POST", "/memories/search", json={"user_id": user_id, "query": query, "top_k": top_k, "agent_id": agent_id, "filters": filters or {}})
        return response.json()

    def export(self, *, user_id: str, agent_id: str | None = None) -> dict[str, Any]:
        params = {"user_id": user_id, **({"agent_id": agent_id} if agent_id else {})}
        response = self._request("GET", "/memories/export", params=params)
        return response.json()

    def delete(self, memory_id: str) -> None:
        self._request("DELETE", f"/memories/{memory_id}")

    def delete_user(self, *, user_id: str, agent_id: str | None = None) -> None:
        params = {"user_id": user_id, **({"agent_id": agent_id} if agent_id else {})}
        self._request("DELETE", "/memories", params=params)

    def request_user_deletion(
        self,
        *,
        user_id: str,
        agent_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        response = self._request(
            "POST",
            "/platform/deletion-jobs",
            json={"user_id": user_id, "agent_id": agent_id},
            headers={"Idempotency-Key": idempotency_key or uuid.uuid4().hex},
        )
        return response.json()

    def create_subject_token(
        self,
        *,
        user_id: str,
        agent_id: str | None = None,
        scopes: list[str] | None = None,
        ttl_seconds: int = 900,
    ) -> dict[str, Any]:
        response = self._request(
            "POST",
            "/platform/tokens",
            json={
                "user_id": user_id,
                "agent_id": agent_id,
                "scopes": scopes or ["memories:read", "memories:write"],
                "ttl_seconds": ttl_seconds,
            },
        )
        return response.json()

    def audit_events(
        self,
        *,
        limit: int = 100,
        action: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        params = {
            "limit": limit,
            **({"action": action} if action else {}),
            **({"user_id": user_id} if user_id else {}),
        }
        return self._request("GET", "/platform/audit", params=params).json()

    def create_webhook(self, url: str, *, event_types: list[str] | None = None) -> dict[str, Any]:
        response = self._request("POST", "/webhooks", json={"url": url, "event_types": event_types or ["memory.ingest.succeeded"]})
        return response.json()

    def list_webhooks(self) -> dict[str, Any]:
        return self._request("GET", "/webhooks").json()

    def webhook_deliveries(self, *, webhook_id: str | None = None, limit: int = 100) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if webhook_id:
            params["webhook_id"] = webhook_id
        return self._request("GET", "/webhooks/deliveries", params=params).json()

    def delete_webhook(self, webhook_id: str) -> None:
        self._request("DELETE", f"/webhooks/{webhook_id}")


class AsyncMemoryClient(_BaseClient):
    """Async client for FastAPI, LangGraph and other async agent runtimes."""

    def __init__(self, api_key: str, *, base_url: str = DEFAULT_BASE_URL, timeout: float = 20.0):
        super().__init__(api_key, base_url=base_url, timeout=timeout)
        self._client = httpx.AsyncClient(base_url=self._base_url, headers=self._headers, timeout=self._timeout)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncMemoryClient":
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            response = await self._client.request(method, path, **kwargs)
        except httpx.TimeoutException as exc:
            raise APITimeoutError("Syntarus API request timed out.") from exc
        except httpx.RequestError as exc:
            raise APIConnectionError("Could not connect to the Syntarus API.") from exc
        _raise_for_response(response)
        return response

    async def add(self, *, user_id: str, messages: list[dict[str, str]], agent_id: str | None = None, run_id: str | None = None, metadata: dict[str, Any] | None = None, idempotency_key: str | None = None) -> dict[str, Any]:
        response = await self._request("POST", "/memories", json=self._payload(user_id, messages, agent_id, run_id, metadata), headers={"Idempotency-Key": idempotency_key or uuid.uuid4().hex})
        return response.json()

    async def event(self, event_id: str) -> dict[str, Any]:
        response = await self._request("GET", f"/events/{event_id}")
        return response.json()

    async def wait_for_event(self, event_id: str, *, timeout: float = 60.0, poll_interval: float = 0.5) -> dict[str, Any]:
        if timeout <= 0 or poll_interval <= 0:
            raise ValueError("timeout and poll_interval must be positive")
        deadline = time.monotonic() + timeout
        while True:
            event = await self.event(event_id)
            if event.get("status") == "succeeded":
                return event
            if event.get("status") in {"dead_letter", "cancelled"}:
                raise EventFailedError(event)
            if time.monotonic() >= deadline:
                raise APITimeoutError(f"Timed out waiting for event {event_id}.")
            await asyncio.sleep(min(poll_interval, max(0.0, deadline - time.monotonic())))

    async def search(self, query: str, *, user_id: str, top_k: int = 10, agent_id: str | None = None, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        """Async provenance-filtered search (enforced by API v1.1+)."""
        response = await self._request("POST", "/memories/search", json={"user_id": user_id, "query": query, "top_k": top_k, "agent_id": agent_id, "filters": filters or {}})
        return response.json()

    async def export(self, *, user_id: str, agent_id: str | None = None) -> dict[str, Any]:
        params = {"user_id": user_id, **({"agent_id": agent_id} if agent_id else {})}
        response = await self._request("GET", "/memories/export", params=params)
        return response.json()

    async def delete(self, memory_id: str) -> None:
        await self._request("DELETE", f"/memories/{memory_id}")

    async def delete_user(self, *, user_id: str, agent_id: str | None = None) -> None:
        params = {"user_id": user_id, **({"agent_id": agent_id} if agent_id else {})}
        await self._request("DELETE", "/memories", params=params)

    async def request_user_deletion(
        self,
        *,
        user_id: str,
        agent_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        response = await self._request(
            "POST",
            "/platform/deletion-jobs",
            json={"user_id": user_id, "agent_id": agent_id},
            headers={"Idempotency-Key": idempotency_key or uuid.uuid4().hex},
        )
        return response.json()

    async def create_subject_token(
        self,
        *,
        user_id: str,
        agent_id: str | None = None,
        scopes: list[str] | None = None,
        ttl_seconds: int = 900,
    ) -> dict[str, Any]:
        response = await self._request(
            "POST",
            "/platform/tokens",
            json={
                "user_id": user_id,
                "agent_id": agent_id,
                "scopes": scopes or ["memories:read", "memories:write"],
                "ttl_seconds": ttl_seconds,
            },
        )
        return response.json()

    async def audit_events(
        self,
        *,
        limit: int = 100,
        action: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        params = {
            "limit": limit,
            **({"action": action} if action else {}),
            **({"user_id": user_id} if user_id else {}),
        }
        return (
            await self._request("GET", "/platform/audit", params=params)
        ).json()

    async def create_webhook(self, url: str, *, event_types: list[str] | None = None) -> dict[str, Any]:
        response = await self._request("POST", "/webhooks", json={"url": url, "event_types": event_types or ["memory.ingest.succeeded"]})
        return response.json()

    async def list_webhooks(self) -> dict[str, Any]:
        return (await self._request("GET", "/webhooks")).json()

    async def webhook_deliveries(self, *, webhook_id: str | None = None, limit: int = 100) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if webhook_id:
            params["webhook_id"] = webhook_id
        response = await self._request("GET", "/webhooks/deliveries", params=params)
        return response.json()

    async def delete_webhook(self, webhook_id: str) -> None:
        await self._request("DELETE", f"/webhooks/{webhook_id}")
