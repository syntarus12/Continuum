# OpenClaw

Use the MCP configuration in `mcp.json` or call the local HTTP API from an
OpenClaw sandbox. The memory service remains outside the sandbox: OpenClaw
gets only the context returned by `search`, and the service enforces project
and user isolation.

