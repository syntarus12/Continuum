# Agent framework recipes

These recipes all use the same Continuum contract. They are intentionally
small so you can paste them into an existing agent instead of replacing your
orchestration framework.

## LangChain

Use `SyntarusLangChainMemory` from `langchain.py` around the model call:

```python
memory = SyntarusLangChainMemory(user_id="customer-42", agent_id="support")
context = await memory.load_memory_variables({"input": user_text})
answer = await chain.ainvoke({"input": user_text, **context})
await memory.save_context({"input": user_text}, {"output": answer})
```

## LangGraph

Add `recall_node` near the start of the graph and `remember_node` after the
answer node. Keep `user_id` and (when needed) `agent_id` in graph state.

## Deep Agents

Expose `recall()` as a read-only context tool. Call `remember()` only after a
task reaches a useful checkpoint, passing a stable `run_id`. Do not write
every intermediate thought to long-term memory.

## Hermes

Register two tools in the Hermes tool registry:

```text
syntarus_search(query, user_id, agent_id?)   -> bounded context + provenance
syntarus_remember(user_message, answer, user_id, agent_id?, run_id?)
```

The tool implementation can import `recall` and `remember` from `generic.py`.
Keep the project key in the Hermes process environment.

## OpenClaw and NemoClaw

Use the HTTP API or MCP boundary from the sandbox rather than importing the
backend stores. `integrations/mcp.json` shows the portable MCP command. A
remote agent should call `POST /v1/memories/search` before generation and
`POST /v1/memories` after a completed turn. Bind `user_id` server-side from
the authenticated tenant; never accept an arbitrary end-user identity from a
browser request.

## Tool safety

Search is read-only. Writes are durable and idempotent. Export and deletion
should be exposed only behind your agent's confirmation/approval policy.
