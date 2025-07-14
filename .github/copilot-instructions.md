# Copilot Instructions for Alation AI Agent SDK

## Project Architecture
- **Monorepo** with three main Python packages:
  - `core-sdk`: Core API client and context tools for Alation Data Catalog
  - `dist-langchain`: LangChain integration for AI agent workflows
  - `dist-mcp`: Model Context Protocol (MCP) server for exposing Alation context to AI agents
- Each package has its own `README.md` and `examples/` directory for usage patterns.
- Guides and integration docs are in the `guides/` directory.

## Key Workflows
- **Build/Install**: Each Python package is installable via `pip install <package-dir>` or `pip install <package-name>` from PyPI.
- **MCP Server**: Run with `python -m alation_ai_agent_mcp` or `start-mcp-server` (after installing `alation-ai-agent-mcp`). Supports both STDIO and HTTP (see `server.py`).
- **Environment Variables**: All authentication and Alation instance config is via environment variables (see `guides/authentication.md`).
- **Testing**: Tests are in each package's `tests/` directory. Use `pytest` from the package root.

## Patterns & Conventions
- **Authentication**: Always use environment variables for secrets. Two auth modes: `user_account` and `service_account`.
- **Signatures**: Flexible response shaping via `signature` parameter (see `guides/signature.md`).
- **Tool Registration**: MCP and LangChain integrations register tools dynamically from the SDK instance.
- **Data Products**: YAML schemas for data products (see `product_example.yaml`).
- **No hardcoded secrets**: Never commit credentials; use `.env` or environment variables.

## Integration Points
- **Alation Data Catalog**: All core functionality depends on a live Alation instance.
- **LangChain**: Use `get_langchain_tools` to bridge SDK with LangChain agents.
- **MCP**: Exposes context tools to any MCP-compatible client (Claude Desktop, LibreChat, etc.).
- **Testing with MCP Inspector**: See `guides/mcp/testing_with_mcp_inspector.md` for local/remote server testing.

## Examples
- See `python/core-sdk/examples/` and `python/dist-langchain/examples/` for usage patterns.
- Example: Running MCP server with HTTP:
  ```bash
  python server.py --http --port 8123
  ```
- Example: Using a signature for custom context retrieval:
  ```python
  signature = {"table": {"fields_required": ["name", "title"]}}
  response = sdk.get_context("Show me sales tables", signature)
  ```

## References
- [Authentication Guide](guides/authentication.md)
- [Supported Object Types](guides/supported.md)
- [Integration Planning](guides/planning.md)
- [Signature Usage](guides/signature.md)

---

If you find any unclear or missing conventions, please provide feedback to improve these instructions.
