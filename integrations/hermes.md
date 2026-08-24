# Hermes-style agents

Syntarus fits a registry-driven Hermes agent as two ordinary tools:

- `syntarus_search`: read-only, bounded search for user/agent context;
- `syntarus_remember`: durable write after a completed turn.

The tool schemas should set `additionalProperties: false`, validate `user_id`
against the authenticated account, and never expose the project key to the
model. See `generic.py` for the implementation calls.

