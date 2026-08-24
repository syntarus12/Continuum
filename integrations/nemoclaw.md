# NemoClaw

NemoClaw can use the same MCP/HTTP boundary as any other sandboxed agent.
Expose search as a read-only tool and keep writes in the post-run hook. For a
multi-tenant deployment, derive `user_id` from the NemoClaw identity at the
gateway; do not let a prompt choose a different tenant.

