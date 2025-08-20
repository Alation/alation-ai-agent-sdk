# MCP Integration

The SDK includes built-in support for the Model Context Protocol (MCP), which enables AI models to retrieve knowledge from Alation during inference.

This package provides an MCP server that exposes Alation Data Catalog capabilities to AI agents with support for multiple transport modes.

## Overview

The MCP integration enables:

- Running an MCP-compatible server that provides access to Alation's context capabilities
- Making Alation metadata accessible to any MCP client
- **NEW**: HTTP mode with OAuth authentication for web-based integrations
- Traditional STDIO mode for direct MCP client connections (like Claude Desktop)

## Transport Modes

### STDIO Mode (Default)
- **Use case**: Direct integration with MCP clients like Claude Desktop, Cursor, etc.
- **Authentication**: Environment variables (refresh token or service account)
- **Connection**: Standard input/output communication
- **Best for**: Local development, desktop applications

### HTTP Mode (New)
- **Use case**: Web-based applications, hosted services, microservice architectures
- **Authentication**: OAuth bearer tokens per request
- **Connection**: RESTful HTTP API with MCP-over-HTTP protocol
- **Best for**: Azure Copilot, LibreChat, VS Code

## Quick Reference

### STDIO Mode (Traditional MCP)
```bash
# Start server for MCP clients (Claude Desktop, Cursor, etc.)
start-alation-mcp-server

# With custom configuration  
start-alation-mcp-server \
  --disabled-tools "TOOL1,TOOL2" \
  --enabled-beta-tools "LINEAGE"
```

### HTTP Mode (Web API)
```bash
# Start HTTP server
start-alation-mcp-server --transport http --host 0.0.0.0 --port 8000

# Production configuration
start-alation-mcp-server \
  --transport http \
  --host 0.0.0.0 \
  --port 8000 \
  --external-url https://your-domain.com
```

**Need more details?** See the complete [HTTP Mode Guide](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/mcp/http_mode.md) for web applications and API integrations.

## Prerequisites

- Python 3.10 or higher
- Access to an Alation Data Catalog instance
- A valid refresh token or client_id and secret. For more details, refer to the [Authentication Guide](https://github.com/Alation/alation-ai-agent-sdk/blob/main/guides/authentication.md).

## Setup

### Environment Variables

Set up your environment variables based on the transport mode you plan to use:

```bash
export ALATION_BASE_URL="https://your-alation-instance.com"

# For authentication (required for both modes)
export ALATION_AUTH_METHOD="user_account"
export ALATION_USER_ID="12345"
export ALATION_REFRESH_TOKEN="your-refresh-token"

# Alternatively, for service account authentication
export ALATION_AUTH_METHOD="service_account"
export ALATION_CLIENT_ID="your-client-id"
export ALATION_CLIENT_SECRET="your-client-secret"

# Optional configuration
export ALATION_DISABLED_TOOLS="tool1,tool2"  # Disable specific tools
export ALATION_ENABLED_BETA_TOOLS="LINEAGE"  # Enable beta tools

# For HTTP mode only
export MCP_EXTERNAL_URL="https://your-lb.com"  # External URL for OAuth (production deployments)
```

### Method 1: Using `uvx` or `pipx` (Quickest)

#### STDIO Mode (Default)
The quickest way to try out the server in STDIO mode is using `pipx` or `uvx`:

```bash
# Using uvx (recommended)
uvx --from alation-ai-agent-mcp start-alaiton-mcp-server

# Using pipx
pipx run alation-ai-agent-mcp
```

#### HTTP Mode
To run the server in HTTP mode with OAuth authentication:

```bash
# Using uvx (recommended)  
uvx --from alation-ai-agent-mcp start-alaiton-mcp-server --transport http --host 0.0.0.0 --port 8000

# Using pipx
pipx run alation-ai-agent-mcp --transport http --host 0.0.0.0 --port 8000
```

### Method 2: Using pip

1. Install the package: ```pip install alation-ai-agent-mcp```

2. Run the server:

#### STDIO Mode (Default)
```bash
# Option A: Using entry point
start-alation-mcp-server

# Option B: Using Python module
python -m alation_ai_agent_mcp
```

#### HTTP Mode
```bash
# Option A: Using entry point
start-alation-mcp-server --transport http --host 0.0.0.0 --port 8000

# Option B: Using Python module  
python -m alation_ai_agent_mcp --transport http --host 0.0.0.0 --port 8000
```

### Advanced HTTP Mode Configuration

For production deployments, you can configure additional options:

```bash
# Full HTTP mode configuration
start-alation-mcp-server \
  --transport http \
  --host 0.0.0.0 \
  --port 8000 \
  --external-url https://your-load-balancer.com \
  --disabled-tools "TOOL1,TOOL2" \
  --enabled-beta-tools "LINEAGE"
```

**HTTP Mode Options:**
- `--host`: Host to bind the server to (default: 127.0.0.1)
- `--port`: Port to bind the server to (default: 8000)  
- `--external-url`: External URL for OAuth callbacks (for load balancers/proxies)
- `--disabled-tools`: Comma-separated list of tools to disable
- `--enabled-beta-tools`: Comma-separated list of beta tools to enable

> **Note**: 
> - **STDIO Mode**: Starts an MCP server using stdin/stdout. Connect to MCP clients like Claude Desktop, Cursor, or test with MCP Inspector.
> - **HTTP Mode**: Starts a web server with OAuth authentication. Access via HTTP API calls or integrate with web applications.

### Transport Mode Usage Examples

#### STDIO Mode - MCP Clients
Please refer to our guides for specific examples of STDIO mode integration:
- [Using with Claude Desktop](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/mcp/claude_desktop.md)
- [Testing with MCP Inspector](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/mcp/testing_with_mcp_inspector.md)
- [Integrating with LibreChat](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/mcp/librechat.md)
- [Integration with Code Editors](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/mcp/code_editors.md)

#### HTTP Mode - Web Applications

When running in HTTP mode, the server exposes RESTful endpoints compatible with the MCP-over-HTTP protocol:

```bash
# Example: List available tools
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/mcp
```

**Authentication for HTTP Mode:**
- Requires valid Alation access tokens as Bearer tokens
- Tokens are validated against your Alation instance
- Each request is authenticated independently

## Debugging and Development

### Using MCP Inspector (STDIO Mode)

To debug the server in STDIO mode, you can use the [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector):

First clone and build the server:
```bash
git clone https://github.com/Alation/alation-ai-agent-sdk.git
cd python/dist-mcp

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip3 install pdm
pdm install
```

> Make sure you run the npx command from the active venv terminal

Run the MCP inspector:
```bash
npx @modelcontextprotocol/inspector python3 alation_ai_agent_mcp/server.py
```

### Testing HTTP Mode

For testing HTTP mode locally:

1. Start the server in HTTP mode:
```bash
start-alation-mcp-server --transport http --host 127.0.0.1 --port 8000
```

2. Test with a valid token (replace with your Alation access token):
```bash
curl -H "Authorization: Bearer YOUR_ALATION_ACCESS_TOKEN" \
     http://localhost:8000/mcp
```

### Build using Docker

Build the server:
```bash
docker build -t alation-mcp-server .
```

Run in STDIO mode (default):
```bash
docker run --rm alation-mcp-server
```

Run in HTTP mode:
```bash
docker run --rm -p 8000:8000 alation-mcp-server --transport http --host 0.0.0.0 --port 8000
```

## Use Cases

### STDIO Mode
- **Claude Desktop integration**: Direct connection to Claude Desktop app
- **Local development**: Testing and development on local machines
- **Code editors**: Integration with Cursor, VS Code with MCP extensions
- **Command-line tools**: Integration with CLI applications that support MCP

### HTTP Mode  
- **Web applications**: RESTful API integration for web apps
- **Microservices**: Part of a larger microservice architecture
- **Load balanced deployments**: Multiple server instances behind a load balancer
- **Cloud native**: Containerized deployments in Kubernetes or similar platforms
- **Third-party integrations**: API integration with external systems