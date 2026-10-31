# Continuum — Community Edition

![Continuum memory engine](assets/continuum-banner.png)

Continuum is a local, self-hosted memory and continuity layer for AI agents. It combines semantic recall in **Qdrant**, entity relationships in **Neo4j**, working state in **Redis**, and operational state in **Postgres**, behind the same API and Python SDK boundary used by Syntarus.

Community Edition is for local development and proofs of concept. It is not the hosted Syntarus control plane and does not imply managed upgrades, multi-region failover, enterprise SSO, billing, or a vendor-operated SLA.

## Why Continuum

Most agents do not need another chat history. They need the current, relevant, scoped state required to continue work correctly:

- **Correct continuation:** retrieve focused context instead of replaying every transcript.
- **Durable ingestion:** a successful write returns an event; extraction and indexing finish asynchronously.
- **Scoped namespaces:** keep users, projects, and agents isolated.
- **Inspectable behavior:** health checks, local doctor commands, API events, and local stores make the loop observable.
- **Portable boundary:** the Python SDK and MCP server work across agent frameworks without coupling them to the underlying databases.

## Watch the workflow

[![Watch the silent Continuum workflow explainer](assets/continuum-how-it-works.gif)](https://raw.githubusercontent.com/syntarus12/Continuum/main/assets/continuum-how-it-works.mp4)

The walkthrough shows the core loop: capture a turn, extract durable facts, connect them in the graph, organize memory views, and recall the context that changes the next answer.

## Quick start

Requirements:

- Docker Desktop with Compose v2
- Python 3.10+ for the SDK and CLI
- `SARVAM_API_KEY` or `GEMINI_API_KEY` for memory extraction

```bash
git clone https://github.com/syntarus12/Continuum.git
cd Continuum
./scripts/start.sh
```

On Windows PowerShell:

```powershell
git clone https://github.com/syntarus12/Continuum.git
cd Continuum
.\scripts\start.ps1
```

The helper creates `.env`, starts the API and console, waits for `/health` and `/ready`, and prints the local URLs. Database ports are not published to the host.

| Service | URL |
| --- | --- |
| Console | `http://127.0.0.1:5173` |
| API | `http://127.0.0.1:8000` |
| OpenAPI | `http://127.0.0.1:8000/docs` |

You can also start Compose directly:

```bash
docker compose --profile ui up -d --pull missing
```

Stop while keeping data:

```bash
./scripts/stop.sh
```

Check the local environment:

```bash
./scripts/doctor.sh
```

## First memory in five minutes

Install the SDK:

```bash
python -m pip install -e ./sdk
```

Run the example:

```bash
python examples/python/quickstart.py
```

Or use the minimal API pattern:

```python
from syntarus import MemoryClient

with MemoryClient(api_key="sk_mem_community", base_url="http://localhost:8000/v1") as memory:
    accepted = memory.add(
        user_id="demo-user",
        agent_id="demo-agent",
        messages=[{"role": "user", "content": "I prefer short status updates."}],
    )
    memory.wait_for_event(accepted["event_id"])
    result = memory.search(
        "How should I receive updates?",
        user_id="demo-user",
        agent_id="demo-agent",
    )
    print(result["context"])
```

`wait_for_event` matters: an accepted HTTP write means the event was queued, not that extraction has completed.

## CLI

```bash
python -m pip install -e ./sdk

continuum init
continuum doctor
echo "The deploy window is Tuesday morning." | continuum memory add --wait
continuum memory search "deploy window"
```

Useful commands:

```bash
# Use a separate namespace for one command.
continuum memory search "deploy window" --user project_42 --agent release-bot

# Stable output for agents and CI.
continuum --json memory search "deploy window"

# Inspect or update non-secret endpoint settings.
continuum config show
continuum config set-endpoint https://ai.syntarus.com/syntarus-api
```

The CLI stores only endpoint and namespace configuration. It never writes an API key to disk.

## Architecture

```text
Agent / CLI / MCP client
        │
        ▼
Syntarus Python SDK ──► FastAPI memory boundary
        │                        │
        │                        ├── Qdrant  ─ semantic recall
        │                        ├── Neo4j   ─ entities and relationships
        │                        ├── Redis   ─ working state
        │                        └── Postgres ─ operational state
        ▼
Durable ingestion events
```

Applications interact only with the SDK/API. They do not need to know how the backing stores are wired or deployed.

## Agent integrations

The [`integrations/`](integrations/README.md) directory contains copy-and-adapt recipes:

| Runtime | Recipe | Recommended use |
| --- | --- | --- |
| LangChain | `langchain.py` | Recall before the model call, save the finished turn |
| LangGraph | `langgraph.py` | Add recall and remember nodes around a graph |
| Deep Agents | `deep-agents.md` | Bounded context tool and checkpoint pattern |
| Hermes | `hermes.md` | Register search and remember tools |
| OpenClaw | `openclaw.md` | Expose memory through MCP |
| NemoClaw | `nemoclaw.md` | Use the HTTP contract from a sandboxed tool |
| Coding agents | `coding-agent.md` | Recall project decisions and persist verified fixes |
| Any runtime | `generic.py` | Two provider-neutral helpers: `recall()` and `remember()` |

## Local security model

- The default stack binds the API and console to loopback and keeps database ports private.
- `sk_mem_community` is a local development key only.
- `MEMORYOS_ALLOW_OPEN=true` is safe only for loopback development.
- Never use the default Compose file directly on a public host.
- The CLI never stores API keys on disk.

For a loopback database inspection:

```bash
docker compose -f docker-compose.yml -f docker-compose.debug.yml up -d
```

For an advanced, customer-controlled public deployment:

```bash
cp .env.example .env
# Set strong MEMORYOS_API_KEYS, MEMORYOS_SSE_SECRET, SESSION_SECRET,
# NEO4J_PASSWORD, POSTGRES_PASSWORD, DNS name, and TLS settings.
docker compose -f docker-compose.yml -f docker-compose.public.yml --profile public up -d --pull missing
```

The public override disables open development auth and terminates HTTPS through Caddy. Hosted Syntarus remains the recommended production path.

## Data reset

Community Edition volumes use the `continuum_ce_` prefix and do not share data with unrelated Compose stacks.

```bash
docker compose down      # stop, keep data
docker compose down -v   # stop and delete Community Edition data
docker compose logs -f backend
```

## Repository map

```text
console/              Local API/console harness
examples/python/      Python quickstart
integrations/         Framework recipes and MCP configuration
scripts/              Start, stop, install, and doctor helpers
sdk/                  Official Python SDK and CLI
sdk/mcp/              MCP server
docker-compose*.yml   Local, debug, source, and public deployment variants
assets/               Banner and workflow media
```

## Validate your checkout

```bash
docker compose config --quiet
docker compose -f docker-compose.yml -f docker-compose.debug.yml config --quiet

python -m pip install -e ./sdk[test]
python -m pytest sdk/tests -q
```

CI runs the same Compose validation and SDK tests on every push and pull request.

## Scope and limitations

Included:

- FastAPI memory boundary and Python SDK/CLI
- Asynchronous ingestion events
- Search, export, deletion, and event inspection
- Vector, sparse, entity, and graph-backed retrieval
- Local console, doctor workflow, Docker deployment, and CI

Not included:

- Hosted billing, SSO, multi-region failover, or vendor SLAs
- A claim that local benchmark results transfer unchanged to every model, dataset, prompt, or deployment
- A universal agent framework; use the provided integration recipes instead

Procedural memory is planned for a later release. It is intentionally absent from this baseline so the distribution stays small and easy to validate.

## Links

- [Python SDK guide](sdk/README.md)
- [MCP guide](sdk/mcp/README.md)
- [Integration recipes](integrations/README.md)
- [Developer portal](https://www.syntarus.com/pages/developers)
- [API reference](https://www.syntarus.com/pages/api-reference)
- [Security and reliability](https://www.syntarus.com/pages/security)
- [Try hosted Syntarus](https://www.syntarus.com/pages/developers)
- [Apply for the 14-day design-partner pilot](https://www.syntarus.com/pages/enterprise)
- [Release checklist](RELEASING.md)
- [License](LICENSE)

## Contributing

Open an issue first for significant changes. For small fixes, open a pull request from a feature branch with:

1. A clear problem statement
2. Updated documentation when behavior changes
3. Passing `docker compose config` checks
4. Passing `python -m pytest sdk/tests -q`

## License

MIT. See [LICENSE](LICENSE) and [sdk/LICENSE](sdk/LICENSE).
