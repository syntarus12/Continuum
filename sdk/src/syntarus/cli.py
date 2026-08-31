"""Continuum's local-first command line interface."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from .client import DEFAULT_BASE_URL, MemoryClient
from .exceptions import SyntarusError


def _config_path() -> Path:
    return Path(os.environ.get("CONTINUUM_CONFIG", Path.home() / ".config" / "continuum" / "config.json"))


def _config() -> dict[str, Any]:
    try:
        return json.loads(_config_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_config(value: dict[str, Any]) -> None:
    path = _config_path(); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _emit(value: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps({"ok": True, "data": value}, default=str)); return
    if isinstance(value, dict):
        for key, item in value.items(): print(f"{key}: {json.dumps(item, default=str) if isinstance(item, (dict, list)) else item}")
    else: print(value)


def _error(message: str, as_json: bool, code: int) -> int:
    if as_json: print(json.dumps({"ok": False, "error": {"message": message, "code": code}}))
    else: print(f"Error: {message}", file=sys.stderr)
    return code


def _client(args: argparse.Namespace) -> MemoryClient:
    key = args.api_key or os.environ.get("CONTINUUM_API_KEY") or os.environ.get("SYNTARUS_API_KEY")
    if not key: raise ValueError("Set CONTINUUM_API_KEY (or SYNTARUS_API_KEY), or pass --api-key. Keys are never stored in config.")
    return MemoryClient(key, base_url=args.base_url or _config().get("base_url", DEFAULT_BASE_URL), timeout=args.timeout)


def _scope(args: argparse.Namespace) -> dict[str, str | None]:
    return {"user_id": args.user, "agent_id": getattr(args, "agent", None)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="continuum", description="Continuum CLI for durable, project-scoped agent memory.")
    parser.add_argument("--api-key", help="Runtime key. Prefer CONTINUUM_API_KEY.")
    parser.add_argument("--base-url", help="API base URL (for example http://localhost:8000/v1).")
    parser.add_argument("--timeout", type=float, default=20)
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit agent-friendly JSON.")
    commands = parser.add_subparsers(dest="command", required=True)
    auth = commands.add_parser("auth", help="Inspect key configuration.")
    auth.add_subparsers(dest="auth_command", required=True).add_parser("status")
    config = commands.add_parser("config", help="Manage non-secret settings.")
    csub = config.add_subparsers(dest="config_command", required=True); csub.add_parser("show")
    endpoint = csub.add_parser("set-endpoint"); endpoint.add_argument("url")
    memory = commands.add_parser("memory", help="Write, retrieve, and list memory.")
    msub = memory.add_subparsers(dest="memory_command", required=True)
    add = msub.add_parser("add"); add.add_argument("text"); add.add_argument("--user", required=True); add.add_argument("--agent"); add.add_argument("--run"); add.add_argument("--wait", action="store_true")
    search = msub.add_parser("search"); search.add_argument("query"); search.add_argument("--user", required=True); search.add_argument("--agent"); search.add_argument("--top-k", type=int, default=10)
    listing = msub.add_parser("list"); listing.add_argument("--user", required=True); listing.add_argument("--agent")
    graph = commands.add_parser("graph", help="Inspect relationships.")
    show = graph.add_subparsers(dest="graph_command", required=True).add_parser("show"); show.add_argument("--user", required=True); show.add_argument("--agent")
    event = commands.add_parser("event", help="Inspect asynchronous work.")
    esub = event.add_subparsers(dest="event_command", required=True)
    get = esub.add_parser("get"); get.add_argument("event_id")
    wait = esub.add_parser("wait"); wait.add_argument("event_id"); wait.add_argument("--poll", type=float, default=.5)
    doctor = commands.add_parser("doctor", help="Verify connectivity, credentials, and read access."); doctor.add_argument("--user", default="continuum_doctor")
    return parser


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    if "--json" in raw: raw.remove("--json"); raw.insert(0, "--json")
    args = build_parser().parse_args(raw)
    try:
        if args.command == "config":
            if args.config_command == "show": _emit({"base_url": _config().get("base_url", DEFAULT_BASE_URL), "config_path": str(_config_path()), "stores_api_key": False}, args.as_json)
            else: _save_config({**_config(), "base_url": args.url.rstrip("/")}); _emit({"base_url": args.url.rstrip("/")}, args.as_json)
            return 0
        if args.command == "auth":
            source = "flag" if args.api_key else ("environment" if os.environ.get("CONTINUUM_API_KEY") or os.environ.get("SYNTARUS_API_KEY") else None)
            _emit({"authenticated": bool(source), "key_source": source, "endpoint": args.base_url or _config().get("base_url", DEFAULT_BASE_URL), "keys_stored": False}, args.as_json); return 0
        with _client(args) as client:
            if args.command == "memory":
                if args.memory_command == "add":
                    result = client.add(user_id=args.user, agent_id=args.agent, run_id=args.run, messages=[{"role": "user", "content": args.text}])
                    if args.wait: result = client.wait_for_event(result["event_id"])
                elif args.memory_command == "search": result = client.search(args.query, user_id=args.user, agent_id=args.agent, top_k=args.top_k)
                else: result = client.export(**_scope(args))
            elif args.command == "graph": result = client.graph(**_scope(args))
            elif args.command == "event": result = client.event(args.event_id) if args.event_command == "get" else client.wait_for_event(args.event_id, poll_interval=args.poll)
            else:
                probe = client.search("continuum cli connectivity check", user_id=args.user, top_k=1)
                result = {"healthy": True, "endpoint": client._base_url, "read_scope": "verified", "result_count": len(probe.get("results", []))}
        _emit(result, args.as_json); return 0
    except ValueError as exc: return _error(str(exc), args.as_json, 2)
    except SyntarusError as exc: return _error(str(exc), args.as_json, 3)
    except KeyboardInterrupt: return _error("Interrupted.", args.as_json, 130)


if __name__ == "__main__": raise SystemExit(main())
