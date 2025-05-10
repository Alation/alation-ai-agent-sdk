# MCP Integration

The SDK includes built-in support for the Model Context Protocol (MCP), which enables AI models to retrieve knowledge from Alation during inference.

This package provides an MCP server that exposes Alation Data Catalog capabilities to AI agents.

## Overview

The MCP integration enables:

- Running an MCP-compatible server that provides access to Alation's context capabilities
- Making Alation metadata accessible to any MCP client

## Installation

```bash
pip install alation-ai-agent-mcp
```

## Prerequisites

- Python 3.10 or higher
- A valid API Access Token created on your Alation Data Catalog instance

## Running the Server

### Using Environment Variables

Set up your environment variables:

```bash
export ALATION_BASE_URL="https://your-alation-instance.com"
export ALATION_USER_ID="12345"
export ALATION_REFRESH_TOKEN="your-refresh-token"
```

Run the server:

```bash
python -m alation_ai_agent_mcp
```

> Note: Running this command only starts the MCP server - you won't be able to ask questions directly. The server needs to be connected to an MCP client (like Claude Desktop or LibreChat) or tested with the MCP Inspector tool. See the guides below for details on connecting to clients.


### Example Usage with MCP Clients
Please refer to our guides for specific examples of:
- [Using with Claude Desktop](../../guides/mcp/claude_desktop.md)
- [Testing with MCP Inspector](../../guides/mcp/testing_with_mcp_inspector.md)
- [Integrating with LibreChat](../../guides/mcp/librechat.md)
