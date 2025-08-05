# Alation AI Agent SDK - Model Context Protocol (MCP) Integration

This directory contains documentation for working with the Alation AI Agent SDK's Model Context Protocol (MCP) server implementation, which enables seamless integration between Alation's catalog and various AI assistants and frameworks.

## Overview

The Model Context Protocol (MCP) server in this SDK allows AI agents to access Alation metadata and content through natural language queries.

## Quick Start

For quick testing and validation of the MCP server, see:
- [Testing with MCP Inspector](./testing_with_mcp_inspector.md) - Step-by-step guide for testing your server

## Client Integrations

Documentation for integrating with specific clients:
- [Claude Desktop Integration](./claude_desktop.md)
- [LibreChat Integration](./librechat.md)

## Features and Tools

The Alation MCP Server exposes the following tools:

- **`alation_context`** - Retrieve contextual information from Alation's catalog using natural language

## Configuration

The MCP server requires the following environment variables:


### Recommended: Service Account Authentication
```bash
export ALATION_BASE_URL="https://your-alation-instance.com"
export ALATION_AUTH_METHOD="service_account"
export ALATION_CLIENT_ID="your-client-id"
export ALATION_CLIENT_SECRET="your-client-secret"
```

> **Note:** Service account credentials can only be created by Alation admins. If you cannot obtain service account credentials, use user account authentication instead. See [User Account Authentication Guide](../authentication.md#user-account-authentication) for details.


If you cannot obtain service account credentials, see the [User Account Authentication Guide](../authentication.md#user-account-authentication) for instructions on using user account authentication.

See the specific client guides for detailed configuration steps.
