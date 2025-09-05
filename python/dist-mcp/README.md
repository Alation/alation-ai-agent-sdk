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
- **Authentication**: OAuth bearer tokens per request (no pre-configured credentials needed)
- **Connection**: RESTful HTTP API with MCP-over-HTTP protocol
- **Security**: Per-request authentication with Alation OAuth tokens
- **Deployment**: Supports load balancers, reverse proxies, and containerized environments
- **Best for**: Azure OpenAI, LibreChat, VS Code extensions, web applications

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
# Start HTTP server (basic)
start-alation-mcp-server --transport http --host 0.0.0.0 --port 8000

# Production configuration with external URL
start-alation-mcp-server \
  --transport http \
  --host 0.0.0.0 \
  --port 8000 \
  --external-url https://your-domain.com \
  --disabled-tools "TOOL1,TOOL2" \
  --enabled-beta-tools "LINEAGE"

# Docker HTTP mode
docker run \
  -e ALATION_BASE_URL=https://your-instance.alationcloud.com \
  -p 8000:8000 \
  ghcr.io/alation/alation-ai-agent-sdk/alation-mcp-server:latest \
  --transport http --host 0.0.0.0
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
# Required for all modes
export ALATION_BASE_URL="https://your-alation-instance.com"

# Required for STDIO mode only (HTTP mode uses OAuth per-request)
export ALATION_AUTH_METHOD="user_account"
export ALATION_USER_ID="12345"
export ALATION_REFRESH_TOKEN="your-refresh-token"

# Alternatively, for service account authentication (STDIO mode only)
export ALATION_AUTH_METHOD="service_account"
export ALATION_CLIENT_ID="your-client-id"
export ALATION_CLIENT_SECRET="your-client-secret"

# Optional configuration (both modes)
export ALATION_DISABLED_TOOLS="tool1,tool2"  # Disable specific tools
export ALATION_ENABLED_BETA_TOOLS="LINEAGE"  # Enable beta tools

# HTTP mode specific (optional)
export MCP_EXTERNAL_URL="https://your-lb.com"  # External URL for OAuth callbacks
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

When running in HTTP mode, the server exposes MCP-over-HTTP endpoints for integration with web applications and services.

**Authentication for HTTP Mode:**
- Requires valid Alation access tokens as Bearer tokens
- Tokens are validated against your Alation instance
- Each request is authenticated independently

> **Integration**: HTTP mode is designed for integration with MCP clients and web applications, not direct API testing. See our integration guides for specific client examples.

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
pip3 install .
```

> Make sure you run the npx command from the active venv terminal

Run the MCP inspector:
```bash
npx @modelcontextprotocol/inspector python3 alation_ai_agent_mcp/server.py
```

### Testing HTTP Mode

#### Local Testing

1. Start the server in HTTP mode:
```bash
# Using Python
start-alation-mcp-server --transport http --host 127.0.0.1 --port 8000

# Using Docker
docker run \
  -e ALATION_BASE_URL=https://your-instance.alationcloud.com \
  -p 8000:8000 \
  ghcr.io/alation/alation-ai-agent-sdk/alation-mcp-server:latest \
  --transport http --host 0.0.0.0
```

2. Verify the server is running:
```bash
# Check if server is responding (no auth required)
curl http://localhost:8000/

# The server should return basic information about the MCP server
```

> **Note**: Testing MCP tools requires a valid Alation access token and proper MCP client integration. The server endpoints are designed for MCP client consumption, not direct API testing.

#### Production Testing

For production deployments with external URLs:
```bash
# Start with external URL configuration
docker run \
  -e ALATION_BASE_URL=https://your-instance.alationcloud.com \
  -e MCP_EXTERNAL_URL=https://your-domain.com \
  -p 8000:8000 \
  ghcr.io/alation/alation-ai-agent-sdk/alation-mcp-server:latest \
  --transport http --host 0.0.0.0 --external-url https://your-domain.com
```

### Method 3: Using Docker

The Docker image supports both STDIO and HTTP transport modes with comprehensive metadata and security features.

#### Docker - STDIO Mode (Default)
```bash
# Using environment file (recommended)
docker run --env-file .env ghcr.io/alation/alation-ai-agent-sdk/alation-mcp-server:latest

# With explicit environment variables
docker run \
  -e ALATION_BASE_URL=https://your-instance.alationcloud.com \
  -e ALATION_AUTH_METHOD=user_account \
  -e ALATION_USER_ID=123 \
  -e ALATION_REFRESH_TOKEN=your_token \
  ghcr.io/alation/alation-ai-agent-sdk/alation-mcp-server:latest

# With tool configuration
docker run --env-file .env \
  ghcr.io/alation/alation-ai-agent-sdk/alation-mcp-server:latest \
  --disabled-tools "TOOL1,TOOL2" \
  --enabled-beta-tools "LINEAGE"
```

#### Docker - HTTP Mode
```bash
# Basic HTTP mode
docker run \
  -e ALATION_BASE_URL=https://your-instance.alationcloud.com \
  -p 8000:8000 \
  ghcr.io/alation/alation-ai-agent-sdk/alation-mcp-server:latest \
  --transport http --host 0.0.0.0

# Production HTTP mode with custom port and external URL
docker run \
  -e ALATION_BASE_URL=https://your-instance.alationcloud.com \
  -e MCP_EXTERNAL_URL=https://your-load-balancer.com \
  -p 9000:9000 \
  ghcr.io/alation/alation-ai-agent-sdk/alation-mcp-server:latest \
  --transport http --host 0.0.0.0 --port 9000 \
  --disabled-tools "TOOL1,TOOL2" \
  --enabled-beta-tools "LINEAGE"
```

#### Docker Environment Variables

**Required for all modes:**
```bash
ALATION_BASE_URL=https://your-instance.alationcloud.com
```

**Required for STDIO mode only:**
```bash
# User account authentication
ALATION_AUTH_METHOD=user_account
ALATION_USER_ID=12345
ALATION_REFRESH_TOKEN=your_refresh_token

# OR service account authentication
ALATION_AUTH_METHOD=service_account
ALATION_CLIENT_ID=your_client_id
ALATION_CLIENT_SECRET=your_client_secret
```

**Optional for both modes:**
```bash
ALATION_DISABLED_TOOLS=tool1,tool2
ALATION_ENABLED_BETA_TOOLS=LINEAGE,DATA_QUALITY
MCP_EXTERNAL_URL=https://external-host:8000  # For HTTP mode OAuth callbacks
```


#### Building from Source

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
- **Desktop applications**: Any application that can spawn processes and communicate via stdin/stdout

### HTTP Mode  
- **MS Copilot Studio**: use with custom connectors
- **ChatGPT customGPT**
