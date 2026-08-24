# Deep Agents

Treat Syntarus as the durable memory tool for a Deep Agents run:

1. Before planning, call `memories.search` with the user's request.
2. Add only the returned bounded context to the planning prompt.
3. Keep intermediate plans and tool chatter in the run checkpoint, not in
   long-term memory.
4. After the final answer or a meaningful completed milestone, call
   `memories.add` with the user/assistant turn and the run ID.

This preserves a clean user profile while still making long-running tasks
resumable.

