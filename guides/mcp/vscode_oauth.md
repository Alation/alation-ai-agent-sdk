# Connect VS Code to Alation's Hosted MCP Server via OAuth <!-- omit from toc -->

## Overview <!-- omit from toc -->

This guide explains how to connect Visual Studio Code (VS Code) to Alation's hosted Model Context Protocol (MCP) server using OAuth 2.0 authentication. Once configured, GitHub Copilot can access many Alation data catalog tools directly from your editor with user-specific permissions and long-lived authentication.

### In this guide

- [Prerequisites](#prerequisites)
- [Step 1: Register an OAuth Client in Alation](#step-1-register-an-oauth-client-in-alation)
  - [Option A: Using the Alation Web UI (Coming Soon)](#option-a-using-the-alation-web-ui-coming-soon)
  - [Option B: Using the Alation Integration APIs](#option-b-using-the-alation-integration-apis)
- [Step 2: Configure MCP Server in VS Code](#step-2-configure-mcp-server-in-vs-code)
- [Step 3: Authenticate and Connect](#step-3-authenticate-and-connect)
- [Step 4: Enable and use different tools in chat](#step-4-enable-and-use-different-tools-in-chat)

---

## Prerequisites

**Server Admin** access to your Alation instance (required for OAuth client creation)
**VS Code version 1.100 or newer** with **GitHub Copilot subscription** (required for MCP integration)

> learn more at [VS Code MCP Servers Documentation](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)

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
       "name": "mcp-server-vscode",
       "client_type": "confidential",
       "redirect_uris": [
         "https://your-tenant.alationcloud.com/oauth/callback",
           "https://vscode.dev/redirect",
           "vscode://vscode.github-authentication/did-authenticate"
       ],
       "refresh_token_expiry": 259200,
       "access_token_expiry": 3600,
       "pkce_required": true
   }'
   ```

3. Safely store the printed `client_id` and `client_secret`

---

## Step 2: Configure MCP Server in VS Code

Create `.vscode/mcp.json` in your project root with the following configuration:

```json
{
  "servers": {
    "alation-mcp-server": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-oauth",
        "https://YOUR_INSTANCE.alationcloud.com/ai/mcp/"
      ],
      "env": {
        "OAUTH_CLIENT_ID": "your-client-id-from-step-1",
        "OAUTH_CLIENT_SECRET": "your-client-secret-from-step-1",
        "OAUTH_AUTHORIZATION_URL": "https://YOUR_INSTANCE.alationcloud.com/oauth/v1/authorize/",
        "OAUTH_TOKEN_URL": "https://YOUR_INSTANCE.alationcloud.com/oauth/v1/token/",
        "OAUTH_SCOPES": "openid",
        "OAUTH_REDIRECT_URI": "https://vscode.dev/redirect"
      }
    }
  }
}
```

Replace placeholders with your actual values, then reload VS Code window.

---

## Step 3: Authenticate and Connect

1. Open Copilot Chat and click the **Tools** button
2. Find Alation MCP server and click **Authenticate** or **Connect**
3. Your browser will open to Alation's login page
4. Log in with your Alation credentials
5. Return to VS Code - the server should now show as connected

> You might need to reconnect the MCP server after the refresh token is expired.

---

## Step 4: Enable and use different tools in chat

After successful authentication, now you are ready to use the tools within your Alation tenant's MCP server:

1. Click on the **Tools** button in Copilot Chat
2. Enable the Alation tools you want to use
3. Start asking questions just as you would using Alation and Copilot will use tools within the MCP server as needed
