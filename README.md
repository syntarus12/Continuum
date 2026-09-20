# Continuum — Community Edition

![Continuum memory engine](assets/continuum-banner.png)

Run a production-style memory service locally, then connect it to the agent
framework you already use. Continuum is the self-hosted learning and
development distribution of the Continuum memory engine: Qdrant for semantic
recall, Neo4j for relationships, Redis for working state, and the Syntarus
API/SDK at the boundary.

It is intentionally simple to start and easy to remove. Your data stays in
the Docker volumes on your machine. The application never needs to know how
Qdrant, Neo4j, Redis, or Postgres are wired together.

Community Edition is a local development distribution, not the hosted
Syntarus control plane. It gives you the same API boundary and a safe place to
prototype before moving a proven workflow to managed Syntarus.

## See how Continuum works

[![Watch the silent Continuum workflow explainer](assets/continuum-how-it-works.gif)](https://raw.githubusercontent.com/syntarus12/Continuum/main/assets/continuum-how-it-works.mp4)

A short, silent walkthrough of the memory loop: capture a turn, extract
durable facts, connect them in a graph, organize the memory views, and recall
the exact context that changes an agent's answer. The preview plays inline;
click it to download the full-resolution MP4.

## Start locally in one command

Requirements:

- Docker Desktop with Compose v2
- A provider key (`SARVAM_API_KEY` or `GEMINI_API_KEY`) for the first memory
  loop. The API, console, health checks, and documentation still start without
  one, but writes remain pending and eventually become `dead_letter` until an
  extraction provider is configured.

From a cloned checkout:

```bash
./scripts/start.sh               # macOS/Linux
# Windows PowerShell:
.\scripts\start.ps1
```

The start helper creates `.env` if needed, launches the API and local console,
waits for `/health` and `/ready`, and prints the final URLs. It does not expose
Qdrant, Neo4j, Redis, or Postgres to the host.

If you are working inside the Syntarus monorepo, the helper automatically uses
the sibling `backend/` source. A normal public checkout uses the released
backend image, so it does not need the private engine source.

If you prefer Compose directly:

```bash
docker compose --profile ui up -d --pull missing
```

Open the local console at `http://127.0.0.1:5173`. The API is at
`http://127.0.0.1:8000` and OpenAPI is at `http://127.0.0.1:8000/docs`.

To stop without deleting data:

```bash
./scripts/stop.sh
```

To run the environment checks at any time:

```bash
./scripts/doctor.sh
```

On Windows, use `scripts\stop.ps1` and `scripts\doctor.ps1`.

## Zero-to-local install

On macOS/Linux, a fresh checkout and start can be done with:

```bash
curl -fsSL https://raw.githubusercontent.com/syntarus12/Continuum/main/scripts/install.sh | bash
```

The installer clones into `./continuum`, creates local-only defaults, and
starts the stack. Review the script before using it in a sensitive environment.

## Local console

The console is intentionally small: it checks health, writes one memory, waits
for the ingestion event, and searches it back. It also links to the hosted
Syntarus developer console, API reference, and the 14-day design-partner pilot.

For the first write → ingest → search loop, copy one provider key into `.env`
and restart:

```bash
SARVAM_API_KEY=...
# or
GEMINI_API_KEY=...
```

The local API key is `sk_mem_community` by default and is valid only on the
loopback development path. Never reuse it on a shared or internet-facing host.

## Optional database inspection

Database ports are private by default. If you need to inspect them locally,
use the explicit debug override:

```bash
docker compose -f docker-compose.yml -f docker-compose.debug.yml up -d
```

This publishes the database ports to `127.0.0.1` only. Do not use the debug
override on a public host.

## Public deployment (advanced)

Do not expose the default Compose file directly to the internet. For a
customer-controlled deployment, set strong secrets and a DNS name in `.env`,
then use the Caddy override:

```bash
docker compose -f docker-compose.yml -f docker-compose.public.yml --profile public up -d --pull missing
```

The public override disables open development auth, keeps databases private,
and terminates HTTPS through Caddy. It is an advanced deployment path; the
hosted Syntarus service is the recommended production path.

## Continuum CLI

Continuum includes a small command-line workflow for developers, coding agents,
and CI. The shortest local path is:

```bash
python -m pip install -e ./sdk

continuum init
continuum doctor
continuum memory add "Customer prefers Hindi" --wait
continuum memory search "language preference"
```

`continuum init` saves only the local endpoint and demo scope. It never stores
an API key. For the local `.env.example` setup, the CLI safely uses
`sk_mem_community` only when the endpoint is `localhost`; hosted or remote
endpoints always require `CONTINUUM_API_KEY` (or `--api-key`).

Useful shortcuts:

```bash
# Read memory text from a pipe.
echo "The deploy window is Tuesday morning." | continuum memory add --wait

# Use a separate namespace without changing config.
continuum memory search "deploy window" --user project_42 --agent release-bot

# Give an agent/CI job stable JSON instead of human output.
continuum --json memory search "language preference"

# Inspect or change the non-secret endpoint settings.
continuum config show
continuum config set-endpoint https://ai.syntarus.com/syntarus-api
```

The CLI never writes API keys to disk. See the [SDK guide](sdk/README.md) for
the full command reference.

The local development key is `sk_mem_community`. It is accepted only because
the example `.env` uses `MEMORYOS_ALLOW_OPEN=true`. Replace that setting and
configure `MEMORYOS_API_KEYS` before exposing the service beyond your
machine.

## First memory in five minutes

Install the SDK from this checkout and run the example:

```bash
python -m venv .venv
python -m pip install -e ./sdk
set SYNTARUS_API_KEY=sk_mem_community       # Windows PowerShell: $env:...
python examples/python/quickstart.py
```

The example writes one turn, waits for the durable ingestion event, and then
searches it back. `wait_for_event` is important: a successful HTTP write means
the event was accepted, not that extraction has finished.

```python
from syntarus import MemoryClient

with MemoryClient(api_key="sk_mem_community", base_url="http://localhost:8000/v1") as memory:
    accepted = memory.add(
        user_id="demo-user",
        agent_id="demo-agent",
        messages=[{"role": "user", "content": "I prefer short status updates."}],
    )
    memory.wait_for_event(accepted["event_id"])
    print(memory.search("How should I receive updates?", user_id="demo-user")["context"])
```

## The integration pattern

Every agent framework follows the same three calls. Keep the API key on the
server or local agent process, never in a browser or mobile bundle.

```text
user message
     │
     ├─ memories.search(query, user_id, agent_id) ──► context for the model
     │                                                   │
     └─ model / tools / agent graph ◄────────────────────┘
             │
             └─ memories.add(turn, run_id) ──► durable background extraction
```

Use a stable `user_id` for the person or tenant, a stable `agent_id` for each
agent that should have an isolated memory namespace, and a `run_id` for one
conversation or job. Omit `agent_id` only when all agents should share the
same user profile.

## Agent framework recipes

The `integrations/` directory contains copy-and-adapt recipes. They are
deliberately provider-neutral: use OpenAI, Anthropic, Gemini, Groq, Sarvam,
Ollama, or a self-hosted model without changing the memory layer.

| Runtime | What is included | Recommended use |
|---|---|---|
| LangChain | `langchain.py` and a small history adapter | Add memory before the model call and save after it |
| LangGraph | `langgraph.py` nodes | Put recall and remember nodes around your graph |
| Deep Agents | `deep-agents.md` | Add memory as a bounded context tool and checkpoint |
| Hermes | `hermes.md` | Register `syntarus_search` and `syntarus_remember` tools |
| OpenClaw | `openclaw.md` + MCP snippet | Expose search/remember through the MCP tool boundary |
| NemoClaw | `nemoclaw.md` | Use the same HTTP contract from a sandboxed tool |
| Coding agents | `coding-agent.md` | Recall project decisions before planning and save verified fixes |
| Any agent | `generic.py` | Two functions: `recall()` and `remember()` |

LangChain and LangGraph examples are runnable when their optional packages
are installed. The Deep Agents, Hermes, OpenClaw, and NemoClaw recipes use
their documented tool/MCP boundaries rather than pretending there is one
universal Python API. That keeps the examples honest as those projects evolve.

## Local data and reset

Continuum uses volume names prefixed with `continuum_ce_`; it will not
reuse or delete the volumes from the main development or production compose
files.

```bash
docker compose down                  # stop containers, keep data
docker compose down -v               # delete Community Edition data
docker compose logs -f backend       # inspect ingestion and API errors
```

The default stack does not publish Qdrant, Neo4j, Redis, or Postgres ports at
all; services communicate on a private Compose network. Use
`docker-compose.debug.yml` only for loopback debugging. For a real deployment,
use the public override, private networking, strong database passwords,
`MEMORYOS_ALLOW_OPEN=false`, and a scoped project key.

## What is included — and what is not

Included:

- the same FastAPI memory API and official Python SDK boundary;
- asynchronous ingestion events, idempotent writes, search, export, and
  deletion;
- vector, sparse, entity, and graph-backed retrieval from the local stores;
- a local console and health/doctor workflow for the first memory loop;
- versioned Community Edition Docker image release workflow;
- examples for common agent runtimes and an MCP configuration pattern;
- isolated local volumes and a reset command for development.

## Roadmap

The current Community Edition focuses on making the core memory loop easy to
run and inspect. First-class procedural memory is planned for a later release;
it is intentionally not part of this baseline so the local distribution stays
small, predictable, and easy to validate.

Continuum is not the hosted Syntarus control plane. Hosted-only
features such as managed upgrades, multi-region failover, hosted billing,
enterprise SSO, and a vendor-operated SLA are not implied by this repository.
The benchmark numbers in this repository are reproducibility material, not a
guarantee for every model, dataset, hardware setup, or prompt.

## Useful links

- [Python SDK](sdk/README.md)
- [API reference](https://www.syntarus.com/pages/api-reference)
- [Developer console](https://www.syntarus.com/pages/developers)
- [Security and reliability](https://www.syntarus.com/pages/security)
- [Try hosted Syntarus](https://www.syntarus.com/pages/developers)
- [Apply for the 14-day design-partner pilot](https://www.syntarus.com/pages/enterprise)
- [Community Edition release checklist](RELEASING.md)
- [Project license](sdk/LICENSE)
