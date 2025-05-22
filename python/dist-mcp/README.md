# MCP Integration

The SDK includes built-in support for the Model Context Protocol (MCP), which enables AI models to retrieve knowledge from Alation during inference.

This package provides an MCP server that exposes Alation Data Catalog capabilities to AI agents.

## Overview

The MCP integration enables:

- Running an MCP-compatible server that provides access to Alation's context capabilities
- Making Alation metadata accessible to any MCP client

## Prerequisites

- Python 3.10 or higher
- Access to an Alation Data Catalog instance
- A valid refresh token or client_id and secret. For more details, refer to the [Authentication Guide](https://github.com/Alation/alation-ai-agent-sdk/blob/main/guides/authentication.md).

## Setup

### Method 1: Using `uvx` or `pipx` (Quickest)
The quickest way to try out the server is using `pipx` or `uvx`

Set up your environment variables:

```bash
export ALATION_BASE_URL="https://your-alation-instance.com"
export ALATION_AUTH_METHOD="user_account"
export ALATION_USER_ID="12345"
export ALATION_REFRESH_TOKEN="your-refresh-token"

# Alternatively, for service account authentication
export ALATION_AUTH_METHOD="service_account"
export ALATION_CLIENT_ID="your-client-id"
export ALATION_CLIENT_SECRET="your-client-secret"
```

To run the Alation MCP Server, use [uvx](https://docs.astral.sh/uv/guides/tools/) (recommend), use the following command:

```bash
uvx --from alation-ai-agent-mcp start-mcp-server
```
If you prefer to use `pipx`, run the following command:
```bash
pipx run alation-ai-agent-mcp
```

### Method 2: Using pip
1. Install the package: ```pip install alation-ai-agent-mcp```
2. Run the server:
```
# Option A: Using entry point
start-mcp-server

# Option B: Using Python module
python -m alation_ai_agent_mcp
```

> Note: Running this command only starts the MCP server - you won't be able to ask questions directly. The server needs to be connected to an MCP client (like Claude Desktop or LibreChat) or tested with the MCP Inspector tool. See the guides below for details on connecting to clients.


### Example Usage with MCP Clients
Please refer to our guides for specific examples of:
- [Using with Claude Desktop](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/mcp/claude_desktop.md)
- [Testing with MCP Inspector](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/mcp/testing_with_mcp_inspector.md)
- [Integrating with LibreChat](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/mcp/librechat.md)

## Debugging the Server

To debug the server, you can use the [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector)

First clone and build the server
```bash
git clone https://github.com/Alation/alation-ai-agent-sdk.git
cd python/dist-mcp
```
```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```
Install dependencies
```bash
pip3 install pdm
pdm install
```

> Make sure you run the npx command from the active venv terminal

Run the MCP inspector
```bash
npx @modelcontextprotocol/inspector python3 alation_ai_agent_mcp/server.py
```

### Build using Docker

First build the server
```
docker build -t alation-mcp-server .
```

Run the following command in your terminal:
```
docker run --rm alation-mcp-server
```