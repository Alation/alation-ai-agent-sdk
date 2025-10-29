# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Architecture

This is the Alation AI Agent SDK for Python, structured as a monorepo with three main packages:

### Core Packages

1. **core-sdk/** - `alation-ai-agent-sdk` (v1.0.0rc1)
   - Main SDK for accessing Alation Data Catalog metadata
   - Core functionality: context retrieval, data products, catalog asset updates
   - Source: `core-sdk/alation_ai_agent_sdk/`

2. **dist-langchain/** - `alation-ai-agent-langchain` (v1.0.0rc1)
   - LangChain integration wrapper around the core SDK
   - Provides LangChain-compatible tools and toolkit
   - Source: `dist-langchain/alation_ai_agent_langchain/`

3. **dist-mcp/** - `alation-ai-agent-mcp` (v1.0.0rc1)
   - Model Context Protocol (MCP) server implementation
   - Supports both STDIO and HTTP transport modes
   - Provides CLI entry point: `start-alation-mcp-server`
   - Source: `dist-mcp/alation_ai_agent_mcp/`

### Key Architecture Components

**Core SDK Components** (`core-sdk/alation_ai_agent_sdk/`):
- `sdk.py` - Main AlationAIAgentSDK class
- `api.py` - REST API client for Alation
- `tools.py` - Tool definitions and implementations
- `data_dict.py` - Data dictionary operations
- `data_product.py` - Data product management
- `lineage.py` - Lineage functionality
- `fields.py` - Custom field operations
- `types.py` - Type definitions and authentication parameters
- `event.py` - Event tracking
- `utils.py` - Utility functions
- `errors.py` - Custom exception classes

**Integration Layers**:
- LangChain: Wraps core SDK tools as LangChain-compatible tools
- MCP: Exposes SDK functionality via Model Context Protocol for AI clients

## Development Commands

### Testing
```bash
# Test all packages
cd core-sdk && pytest tests/
cd dist-langchain && pytest tests/
cd dist-mcp && pytest tests/

# Or using PDM scripts
cd core-sdk && pdm run test
cd dist-langchain && pdm run test
cd dist-mcp && pdm run test
```

### Code Quality
```bash
# Lint and format all projects (from repository root)
python scripts/verify_and_format_changes.py

# Manual linting per project
ruff check --fix core-sdk/
ruff check --fix dist-langchain/
ruff check --fix dist-mcp/

# Manual formatting per project
ruff format core-sdk/
ruff format dist-langchain/
ruff format dist-mcp/
```

### Package Management
Each package uses PDM with `pyproject.toml`. All packages require Python 3.10+.

```bash
# Install dependencies for development
cd core-sdk && pdm install --dev
cd dist-langchain && pdm install --dev
cd dist-mcp && pdm install --dev

# Build packages
cd core-sdk && pdm build
cd dist-langchain && pdm build
cd dist-mcp && pdm build
```

### MCP Server Development
```bash
# STDIO mode (default, for MCP clients like Claude Desktop)
start-alation-mcp-server

# HTTP mode (for web applications, OAuth per-request)
start-alation-mcp-server --transport http --host 0.0.0.0 --port 8000

# Development with MCP Inspector (STDIO mode)
npx @modelcontextprotocol/inspector python3 dist-mcp/alation_ai_agent_mcp/server.py
```

## Authentication

The SDK supports one authentication method:

1. **Service Account (recommended)**:
   ```python
   ServiceAccountAuthParams(client_id="...", client_secret="...")
   ```

For MCP HTTP mode, authentication is handled per-request via OAuth bearer tokens.

## Key Files

- `openapi.yaml` - API specification for Alation endpoints
- `scripts/verify_and_format_changes.py` - Development workflow script for linting, formatting, and version management
- Each package has its own `pyproject.toml` with dependencies and build configuration
- Examples are located in `{package}/examples/` directories

## Important Notes

- All three packages maintain synchronized version numbers (currently 0.12.0)
- The core SDK is the foundation; LangChain and MCP packages depend on it
- When making changes, ensure version bumps are coordinated across packages that are affected
- The MCP server can run in two modes: STDIO (for direct MCP clients) and HTTP (for web integrations)
- The repository includes comprehensive examples for each integration type

## Testing Integration

For integration testing, you'll need:
- Access to an Alation Data Catalog instance
- Valid authentication credentials (service account or refresh token)
- Environment variables set according to the authentication method chosen