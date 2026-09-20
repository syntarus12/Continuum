"""Continuum's local-first command line interface.

The CLI is deliberately small: initialize a local endpoint, add a memory,
search it back, and use ``--json`` when an agent or CI job needs a stable
machine-readable response. API keys are never written to the config file.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from .client import DEFAULT_BASE_URL, MemoryClient
from .exceptions import SyntarusError

LOCAL_BASE_URL = "http://localhost:8000/v1"
LOCAL_API_KEY = "sk_mem_community"


def _config_path() -> Path:
    return Path(os.environ.get("CONTINUUM_CONFIG", Path.home() / ".config" / "continuum" / "config.json"))


def _config() -> dict[str, Any]:
    try:
        return json.loads(_config_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_config(value: dict[str, Any]) -> None:
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _base_url(args: argparse.Namespace) -> str:
    return (args.base_url or _config().get("base_url") or DEFAULT_BASE_URL).rstrip("/")


def _is_local(url: str) -> bool:
    host = url.split("://", 1)[-1].split("/", 1)[0].split(":", 1)[0].lower()
    return host in {"localhost", "127.0.0.1"}


def _default_scope(name: str, fallback: str) -> str:
    config_key = name.lower()
    return os.environ.get(name) or _config().get(config_key) or fallback


def _api_key(args: argparse.Namespace) -> tuple[str | None, str | None]:
    if args.api_key:
        return args.api_key, "flag"
    if os.environ.get("CONTINUUM_API_KEY"):
        return os.environ["CONTINUUM_API_KEY"], "environment"
    # This key is only accepted by the local .env.example configuration.
    if _is_local(_base_url(args)):
        return LOCAL_API_KEY, "local-dev"
    if os.environ.get("SYNTARUS_API_KEY"):
        return os.environ["SYNTARUS_API_KEY"], "environment"
    return None, None


def _emit(value: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps({"ok": True, "data": value}, default=str))
    elif isinstance(value, dict):
        for key, item in value.items():
            rendered = json.dumps(item, default=str) if isinstance(item, (dict, list)) else item
            print(f"{key}: {rendered}")
    else:
        print(value)


def _error(message: str, as_json: bool, code: int) -> int:
    if as_json:
        print(json.dumps({"ok": False, "error": {"message": message, "code": code}}))
    else:
        print(f"Error: {message}", file=sys.stderr)
    return code


def _client(args: argparse.Namespace) -> MemoryClient:
    key, _source = _api_key(args)
    if not key:
        raise ValueError("Set CONTINUUM_API_KEY (or SYNTARUS_API_KEY), or pass --api-key. Keys are never stored in config.")
    return MemoryClient(key, base_url=_base_url(args), timeout=args.timeout)


def _scope(args: argparse.Namespace) -> dict[str, str | None]:
    return {
        "user_id": args.user or _default_scope("CONTINUUM_USER_ID", "demo-user"),
        "agent_id": getattr(args, "agent", None) or _default_scope("CONTINUUM_AGENT_ID", "demo-agent"),
    }


def _human(command: str, args: argparse.Namespace, value: Any) -> None:
    """Keep default output useful to a person; --json remains machine-stable."""
    if command == "memory add" and isinstance(value, dict):
        event_id = value.get("event_id") or value.get("id")
        print(f"Memory accepted for {args.user}.")
        if event_id:
            print(f"Event: {event_id}")
        if args.wait:
            print(f"Memory ready: {value.get('status', 'succeeded')}.")
        return
    if command == "memory search" and isinstance(value, dict):
        context = value.get("context")
        if context:
            print(context if isinstance(context, str) else json.dumps(context, indent=2, default=str))
            return
        results = value.get("results") or []
        print(f"{len(results)} memories found for {args.user}.")
        for item in results:
            if isinstance(item, dict):
                text = item.get("text") or item.get("memory") or item.get("content")
            else:
                text = item
            if text:
                print(f"- {text}")
        return
    if command == "doctor" and isinstance(value, dict):
        print(f"Continuum is reachable at {value.get('endpoint', _base_url(args))}.")
        print(f"Read check: {value.get('result_count', 0)} memories returned.")
        return
    _emit(value, False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="continuum", description="Continuum CLI for durable agent memory.")
    parser.add_argument("--version", action="version", version="continuum 0.3.0")
    parser.add_argument("--api-key", help="Runtime key. Prefer CONTINUUM_API_KEY.")
    parser.add_argument("--base-url", help="API base URL (for example http://localhost:8000/v1).")
    parser.add_argument("--timeout", type=float, default=20)
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit agent-friendly JSON.")
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="Save the local endpoint and demo scope; no key is stored.")
    init.add_argument("--base-url", default=LOCAL_BASE_URL, help="API base URL (default: http://localhost:8000/v1).")
    init.add_argument("--user", default=os.environ.get("CONTINUUM_USER_ID", "demo-user"))
    init.add_argument("--agent", default=os.environ.get("CONTINUUM_AGENT_ID", "demo-agent"))

    auth = commands.add_parser("auth", help="Inspect key configuration.")
    auth.add_subparsers(dest="auth_command", required=True).add_parser("status")

    config = commands.add_parser("config", help="Manage non-secret settings.")
    csub = config.add_subparsers(dest="config_command", required=True)
    csub.add_parser("show")
    endpoint = csub.add_parser("set-endpoint")
    endpoint.add_argument("url")

    memory = commands.add_parser("memory", help="Write, retrieve, and export memory.")
    msub = memory.add_subparsers(dest="memory_command", required=True)
    add = msub.add_parser("add", help="Remember text; omit text to read stdin.")
    add.add_argument("text", nargs="?")
    add.add_argument("--user", default=_default_scope("CONTINUUM_USER_ID", "demo-user"))
    add.add_argument("--agent", default=_default_scope("CONTINUUM_AGENT_ID", "demo-agent"))
    add.add_argument("--run")
    add.add_argument("--wait", action="store_true", help="Wait until extraction has completed.")
    search = msub.add_parser("search", help="Recall relevant memory.")
    search.add_argument("query")
    search.add_argument("--user", default=_default_scope("CONTINUUM_USER_ID", "demo-user"))
    search.add_argument("--agent", default=_default_scope("CONTINUUM_AGENT_ID", "demo-agent"))
    search.add_argument("--top-k", type=int, default=10)
    listing = msub.add_parser("list", help="Export a memory namespace.")
    listing.add_argument("--user", default=_default_scope("CONTINUUM_USER_ID", "demo-user"))
    listing.add_argument("--agent", default=_default_scope("CONTINUUM_AGENT_ID", "demo-agent"))

    graph = commands.add_parser("graph", help="Inspect relationships.")
    show = graph.add_subparsers(dest="graph_command", required=True).add_parser("show", help="Show a user's graph.")
    show.add_argument("--user", default=_default_scope("CONTINUUM_USER_ID", "demo-user"))
    show.add_argument("--agent", default=_default_scope("CONTINUUM_AGENT_ID", "demo-agent"))

    event = commands.add_parser("event", help="Inspect asynchronous work.")
    esub = event.add_subparsers(dest="event_command", required=True)
    get = esub.add_parser("get")
    get.add_argument("event_id")
    wait = esub.add_parser("wait")
    wait.add_argument("event_id")
    wait.add_argument("--poll", type=float, default=.5)

    doctor = commands.add_parser("doctor", help="Verify connectivity, credentials, and read access.")
    doctor.add_argument("--user", default=_default_scope("CONTINUUM_USER_ID", "demo-user"))
    doctor.add_argument("--agent", default=_default_scope("CONTINUUM_AGENT_ID", "demo-agent"))
    return parser


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    if "--json" in raw:
        raw.remove("--json")
        raw.insert(0, "--json")
    args = build_parser().parse_args(raw)
    try:
        if args.command == "init":
            _save_config({**_config(), "base_url": args.base_url.rstrip("/"), "continuum_user_id": args.user, "continuum_agent_id": args.agent})
            _emit({"base_url": args.base_url.rstrip("/"), "user": args.user, "agent": args.agent, "api_key_stored": False}, args.as_json)
            return 0
        if args.command == "config":
            if args.config_command == "show":
                _emit({"base_url": _config().get("base_url", DEFAULT_BASE_URL), "user": _default_scope("CONTINUUM_USER_ID", "demo-user"), "agent": _default_scope("CONTINUUM_AGENT_ID", "demo-agent"), "config_path": str(_config_path()), "stores_api_key": False}, args.as_json)
            else:
                _save_config({**_config(), "base_url": args.url.rstrip("/")})
                _emit({"base_url": args.url.rstrip("/")}, args.as_json)
            return 0
        if args.command == "auth":
            _key, source = _api_key(args)
            _emit({"authenticated": bool(source), "key_source": source, "endpoint": _base_url(args), "keys_stored": False}, args.as_json)
            return 0

        with _client(args) as client:
            if args.command == "memory":
                if args.memory_command == "add":
                    text = args.text
                    if not text and not sys.stdin.isatty():
                        text = sys.stdin.read().strip()
                    if not text:
                        raise ValueError("Provide memory text or pipe it on stdin.")
                    result = client.add(user_id=args.user, agent_id=args.agent, run_id=args.run, messages=[{"role": "user", "content": text}])
                    if args.wait:
                        result = client.wait_for_event(result["event_id"])
                elif args.memory_command == "search":
                    result = client.search(args.query, user_id=args.user, agent_id=args.agent, top_k=args.top_k)
                else:
                    result = client.export(**_scope(args))
            elif args.command == "graph":
                result = client.graph(**_scope(args))
            elif args.command == "event":
                result = client.event(args.event_id) if args.event_command == "get" else client.wait_for_event(args.event_id, poll_interval=args.poll)
            else:
                probe = client.search("continuum cli connectivity check", user_id=args.user, top_k=1)
                result = {"healthy": True, "endpoint": client._base_url, "read_scope": "verified", "result_count": len(probe.get("results", []))}
        if args.as_json:
            _emit(result, True)
        else:
            command = "doctor" if args.command == "doctor" else f"{args.command} {getattr(args, args.command + '_command', '')}".strip()
            _human(command, args, result)
        return 0
    except ValueError as exc:
        return _error(str(exc), args.as_json, 2)
    except SyntarusError as exc:
        return _error(str(exc), args.as_json, 3)
    except KeyboardInterrupt:
        return _error("Interrupted.", args.as_json, 130)


if __name__ == "__main__":
    raise SystemExit(main())
