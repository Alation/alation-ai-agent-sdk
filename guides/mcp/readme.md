# Alation AI Agent SDK - Model Context Protocol (MCP) Integration

This directory contains documentation for working with the Alation AI Agent SDK's Model Context Protocol (MCP) server implementation, which enables seamless integration between Alation's catalog and various AI assistants and frameworks.

## Overview

The Model Context Protocol (MCP) server in this SDK allows AI agents to access Alation metadata and content through natural language queries. The server supports multiple transport modes for different use cases:

### Transport Modes

- **STDIO Mode**: Direct integration with MCP clients (Claude Desktop, Cursor, etc.)
- **HTTP Mode**: RESTful API with OAuth authentication for web applications and microservices

## Quick Start

For quick testing and validation of the MCP server:
- [Testing with MCP Inspector](./testing_with_mcp_inspector.md) - Step-by-step guide for testing your server in STDIO mode
- [HTTP Mode Guide](./http_mode.md) - Complete guide for HTTP mode setup and usage
- [Known Issues](./known_issues.md) - Solutions for common problems (SSL certificates, VPN issues, etc.)

## Client Integrations

### STDIO Mode (Traditional MCP)
Documentation for integrating with MCP clients:
- [Claude Desktop Integration](./claude_desktop.md) - Desktop app integration
- [LibreChat Integration](./librechat.md) - Open-source ChatGPT alternative  
- [Code Editor Integration](./code_editors.md) - VS Code, Cursor integration

## Server Modes

### STDIO Mode (Traditional MCP)
- **Use case**: Direct MCP client connections
- **Authentication**: Environment variables (refresh token or service account)
- **Clients**: Claude Desktop, Cursor, LibreChat, MCP Inspector
- **Protocol**: Standard MCP over stdin/stdout

### HTTP Mode (Web API)
- **Use case**: Web applications, microservices, API integrations
- **Authentication**: OAuth bearer tokens per request
- **Clients**: Azure Copilot, LibreChat, VS Code
- **Protocol**: MCP-over-HTTP with RESTful endpoints

## Features and Tools

The Alation MCP Server exposes the following tools (available in both modes):

- **`alation_context`** - Retrieve contextual information from Alation's catalog using natural language
- **`alation_bulk_retrieval`** - Retrieve multiple catalog objects
- **`get_data_products`** - Access data products information
- **`update_catalog_asset_metadata`** - Update catalog asset metadata
- **`check_job_status`** - Monitor job execution status
- **`get_lineage`** - Retrieve data lineage information
- **`check_data_quality`** - Assess data quality metrics
- **`generate_data_product`** - Create new data products
- **`get_custom_fields_definitions`** - Retrieve custom field definitions
- **`get_data_dictionary_instructions`** - Get data dictionary setup instructions

## Configuration

The MCP server requires the following environment variables:

### For STDIO Mode (Traditional MCP Clients)

#### Recommended: Service Account Authentication
```bash
export ALATION_BASE_URL="https://your-alation-instance.com"
export ALATION_AUTH_METHOD="service_account"
export ALATION_CLIENT_ID="your-client-id"
export ALATION_CLIENT_SECRET="your-client-secret"
```

#### Alternative: User Account Authentication
```bash
export ALATION_BASE_URL="https://your-alation-instance.com"
export ALATION_AUTH_METHOD="user_account"
export ALATION_USER_ID="12345"
export ALATION_REFRESH_TOKEN="your-refresh-token"
```

### For HTTP Mode (Web API)

HTTP mode uses per-request authentication via OAuth bearer tokens. Set up the base configuration:

```bash
export ALATION_BASE_URL="https://your-alation-instance.com"

# Optional: External URL for OAuth (production deployments)
export MCP_EXTERNAL_URL="https://your-load-balancer.com"
```

**Authentication Flow for HTTP Mode:**
1. Client obtains access token from Alation OAuth endpoint
2. Client includes token as `Authorization: Bearer <token>` header
3. Server validates token against Alation instance for each request

### Optional Configuration (Both Modes)

```bash
# Tool configuration
export ALATION_DISABLED_TOOLS="tool1,tool2"  # Disable specific tools
export ALATION_ENABLED_BETA_TOOLS="LINEAGE"  # Enable beta tools
```

> **Note:** Service account credentials can only be created by Alation admins. If you cannot obtain service account credentials, use user account authentication instead. See [User Account Authentication Guide](../authentication.md#user-account-authentication) for details.

## Getting Started

### STDIO Mode
Start the server for MCP client connections:
```bash
start-alation-mcp-server
```

### HTTP Mode  
Start the server as a web API:
```bash
start-alation-mcp-server --transport http --host 0.0.0.0 --port 8000
```

See the specific client guides for detailed integration steps.
