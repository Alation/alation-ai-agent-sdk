# Connect Claude (Web & Desktop) to Alation's Hosted MCP Server via OAuth <!-- omit from toc -->

## Overview <!-- omit from toc -->

This guide explains how to connect Claude to Alation's hosted Model Context Protocol (MCP) server using OAuth 2.0 authentication. Once configured, you can access many Alation data catalog tools directly from Claude in both the web interface (claude.ai) and the Claude Desktop application with user-specific permissions and long-lived authentication.

### In this guide

- [Prerequisites](#prerequisites)
- [Plan-Specific Configuration](#plan-specific-configuration)
  - [Team and Enterprise Plans](#team-and-enterprise-plans)
  - [Pro and Max Plans](#pro-and-max-plans)
- [Step 1: Register an OAuth Client in Alation](#step-1-register-an-oauth-client-in-alation)
  - [Option A: Using the Alation Web UI (Coming Soon)](#option-a-using-the-alation-web-ui-coming-soon)
  - [Option B: Using the Alation Integration APIs](#option-b-using-the-alation-integration-apis)
- [Step 2: Add MCP Server in Claude](#step-2-add-mcp-server-in-claude)
  - [1. Access Connector Settings](#1-access-connector-settings)
  - [2. Add Custom Connector](#2-add-custom-connector)
  - [3. Configure Connection Details](#3-configure-connection-details)
  - [4. Save Configuration](#4-save-configuration)
- [Step 3: Authenticate and Authorize](#step-3-authenticate-and-authorize)
- [Step 4: Enable and use different tools in chat](#step-4-enable-and-use-different-tools-in-chat)

---

## Prerequisites

**Server Admin** access to your Alation instance (required for OAuth client creation)
**Claude Pro, Max, Team, or Enterprise subscription** (required for MCP integration)

> learn more at [Building Custom Connectors via Remote MCP Servers](https://support.claude.com/en/articles/11503834-building-custom-connectors-via-remote-mcp-servers)

---

## Plan-Specific Configuration

The configuration process differs depending on your Claude subscription type:

### Team and Enterprise Plans

For organizations with Team or Enterprise subscriptions:

- Only **Primary Owners** or **Owners** can configure connectors at the organization level
- Once configured, **individual users** can then connect to and enable the connector
- Configuration is done through **Admin Settings** → **Connectors**

### Pro and Max Plans

For individual Pro or Max subscriptions:

- **Users configure connectors themselves** directly in their Claude settings
- Configuration is done through **Settings** → **Connectors**

> Learn more at [Getting Started with Custom Connectors using Remote MCP](https://support.claude.com/en/articles/11175166-getting-started-with-custom-connectors-using-remote-mcp)

---

## Step 1: Register an OAuth Client in Alation

> **Note:**
> This setup requires a Server Admin access to the Alation instance.

### Option A: Using the Alation Web UI (Coming Soon)

UI support to create an OAuth Client is coming soon.

### Option B: Using the Alation Integration APIs

1. Retrieve an API access token
   a. Log in to your Alation catalog.
   b. Click on the User icon in the top right-hand corner and in the menu that opens, select **Proﬁle Settings**.
   ![profile-settings](../openai/images/profile-settings.png)
   c. Click on the **Authentication** tab of the settings.
   d. Use the steps in [Create an API Token via the UI](https://developer.alation.com/dev/docs/authentication-into-alation-apis#create-an-api-access-token-via-the-ui) in Alation’s API docs to get an access token for the Alation public API.
   e. Make a note of the access token to use it for authenticating from your custom GPT.

2. Run the following curl command to create an oauth client for Claude. Replace the `BASE_URL` and `API_TOKEN` with the correct values.

   ```bash
   curl --location '<BASE_URL>/integration/core/v1/oauth/clients/' \
   --header 'token: <API_TOKEN>' \
   --header 'Content-Type: application/json' \
   --data '{
     "name": "mcp-server-claude",
     "client_type": "confidential",
     "redirect_uris": [
         "https://your-tenant.alationcloud.com/oauth/callback",
         "https://claude.ai/api/mcp/auth_callback",
         "https://claude.com/api/mcp/auth_callback"
     ],
     "refresh_token_expiry": 259200,
     "access_token_expiry": 3600,
     "pkce_required": true
   }'
   ```

3. Safely store the returned `client_id` and `client_secret`

---

## Step 2: Add MCP Server in Claude

Now you'll add Alation's hosted MCP server to Claude. This configuration works for Claude web, Claude Desktop, and Claude mobile apps.

### 1. Access Connector Settings

The path to connector settings depends on your Claude plan:

- For Pro and Max Plans, navigate to Settings > Connectors
- For Team and Enterprise Plans, navigate to Admin Settings > Connectors

### 2. Add Custom Connector

1. Click **Add custom connector** button at the bottom of the section
2. You'll see a form with the following fields

### 3. Configure Connection Details

Fill in the connector configuration:

| Field                     | Value                                              | Description                       |
| ------------------------- | -------------------------------------------------- | --------------------------------- |
| **Connector Name**        | `Your Connector Name`                              | Display name for this integration |
| **Remote MCP server URL** | `<https://YOUR_INSTANCE.alationcloud.com/ai/mcp/>` | Your Alation MCP server URL       |
| **Client ID**             | `your-client-id-from-step-1`                       | From OAuth client registration    |
| **Client Secret**         | `your-client-secret-from-step-1`                   | From OAuth client registration    |

### 4. Save Configuration

1. Review all fields for accuracy
2. Click **Add**

---

## Step 3: Authenticate and Authorize

1. Go to your personal settings and click on **Connectors**
2. Click the **Connect** button on the new MCP connector you just added
3. You'll be redirected to your Alation login page on a new browser tab
4. Log in with your Alation credentials
5. Now go back to Claude and the new MCP server will be ready to use

> You might need to reconnect the MCP server after the refresh token is expired.

---

## Step 4: Enable and use different tools in chat

After successful authentication, now you are ready to use the tools within your Alation tenant's MCP server:

1. Click on the **Configure** button next to the newly connected MCP server
2. You can choose to enable/disable/require-approval on any of the listed tools
3. Start a new chat and click on the **Search and Tools** button
4. Make sure that your MCP server is enabled
5. Start asking questions just as you would using Alation and Claude will use tools within the MCP server as needed
