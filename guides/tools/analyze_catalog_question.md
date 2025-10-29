# analyze_catalog_question

An orchestration tool that analyzes questions and provides workflow guidance for LLM agents.

**NOTE** : This tool is designed for LLM orchestration (MCP servers, autonomous agents). For direct Python SDK usage, call ` get_context ` or ` bulk_retrieval ` directly.

**Functionality**

- Analyzes natural language questions about the data catalog
- Determines optimal search strategy (bulk enumeration vs semantic discovery)
- Identifies required metadata gathering steps (custom fields, signatures)
- Returns step-by-step execution instructions for LLMs
- Provides actionability assessment and routing decisions

**Input Parameters**

- ` question ` (string): The natural language query

**Returns**

- Formatted text containing workflow analysis and execution plan

**When to Use**

- MCP server implementations (Claude Desktop)
- Autonomous LLM agents that need query routing logic
- Applications where LLMs orchestrate multiple tool calls
