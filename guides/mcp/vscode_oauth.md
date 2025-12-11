# Connect VS Code to Alation's Hosted MCP Server via OAuth <!-- omit from toc -->

## Overview <!-- omit from toc -->

This guide explains how to connect Visual Studio Code (VS Code) to Alation's hosted Model Context Protocol (MCP) server using OAuth 2.0 authentication. Once configured, GitHub Copilot can access many Alation data catalog tools directly from your editor with user-specific permissions and long-lived authentication.

### In this guide

- [Prerequisites](#prerequisites)
- [Step 1: Register an OAuth Client in Alation](#step-1-register-an-oauth-client-in-alation)
- [Step 2: Configure MCP Server in VS Code](#step-2-configure-mcp-server-in-vs-code)
- [Step 3: Authenticate and Connect](#step-3-authenticate-and-connect)
- [Step 4: Enable and use different tools in chat](#step-4-enable-and-use-different-tools-in-chat)

---

## Prerequisites

**VS Code version 1.100 or newer** with **GitHub Copilot subscription** (required for MCP integration)

>learn more at [VS Code MCP Servers Documentation](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)

---

## Step 1: Register an OAuth Client in Alation

You'll need to register VS Code as an OAuth client application in your Alation instance. Please make sure the JWT token flag is enabled on the tenant:

   ```bash
   alation_conf alation.feature_flags.enable_jwt_in_v1_oauth_stack -s True
   ```

### Option A: Using the Alation Web UI (Placeholder for now, fill in here later once we actually have UI for this)

Once we have UI, we can remove Option B below.

### Option B: Using the Alation Django Shell (Please contact Alation Engineers for this step)

If the Web UI is not available, you can create the OAuth client via Django shell:

1. Access your Alation tenant's pod (via kubectl or SSH)

2. Open Django shell:

   ```bash
   alation_django_shell
   ```

3. Run the following Python code:

   ```python
   import secrets
   from api_authentication.models import Application
   client_id = secrets.token_urlsafe(32)
   client_secret = secrets.token_urlsafe(32)
   app = Application.objects.create(
      name="alation-ai-hosted-mcp-server",
      client_id=client_id,
      client_secret=client_secret,
      client_type="confidential",
      redirect_uris=[
            "https://your-tenant.alationcloud.com/oauth/callback",
            "https://vscode.dev/redirect",
            "vscode://vscode.github-authentication/did-authenticate"
            ],
      refresh_token_expiry=15552000,
      access_token_expiry=86400,
      is_active=True,
      pkce_required=True,
      jwt_required=True,
      internal_application=False
   )
   print(f"client_id: {client_id}")
   print(f"client_secret: {client_secret}")
   ```

   > **Note**: You may see an error message like `Error decrypting value, details: Unknown prefix: None. Only cryiv_enc_str:::, crypt_enc_str::: and scy_enc_str::: are supported., returning the value as is.` This error is safe to ignore - the OAuth client will still be created successfully.

4. Safely store the printed `client_id` and `client_secret`

5. Exit Django shell

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
