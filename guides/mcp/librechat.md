
# Alation Context API Integration – LibreChat MCP Server

This guide explains how to set up and use the **Alation Context API MCP server** with LibreChat. This enables LibreChat to retrieve Alation metadata (e.g., trusted tables, documentation, schema info) contextually during conversations with AI models.

---

## Prerequisites

- **LibreChat** self-hosted environment properly installed
- Python 3.10 or later
- Access to Alation instance with:
  - User ID
  - valid Refresh token

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/Alation/ai-agent-sdk.git
cd ai-agent-sdk
```
### Step 2: Install the required dependencies

```bash
cd python/ai_agent_sdk/dist-mcp
pip install -e ".[all]"
```

---

## Configuration

### Step 4: Add MCP Server Entry in `librechat.yaml`

Edit your `librechat.yaml` configuration to define a new `mcpServer` using the `stdio` protocol.
The LibreChat Docker image includes the [`uv`](https://github.com/astral-sh/uv) package manager by default (from version v0.7.8-rc1).

```yaml
mcpServers:
  alation:
    type: stdio
    command: uv
    args:
      - "-m"
      - "alation_ai_agent_mcp"
    env:
      ALATION_API_BASE: "https://your.alation.instance"
      USER_ID: "3"
      REFRESH_TOKEN: "your-token"
    iconPath: "https://i.postimg.cc/mZVp7vF9/Alation-logo.png"
```
---

## Step 5: Rebuild & Restart LibreChat

After updating `librechat.yaml`, restart LibreChat:

```bash
docker compose down
docker compose up -d
```

Confirm that LibreChat successfully loads the `alation` MCP server. If there are errors, check the logs from `docker compose logs` or MCP output directly.

---

## Verifying the Integration

1. In the LibreChat UI, navigate the the agent builder using the right side navigation bar

<img width="320" alt="Screenshot 2025-05-05 at 8 08 31 PM" src="https://github.com/user-attachments/assets/0a5ec475-4322-4b2f-b78d-997b2a68cae6" />

2. Scroll down to find `Add tools`

<img width="300" alt="Screenshot 2025-05-05 at 8 08 25 PM" src="https://github.com/user-attachments/assets/76886312-9d95-428a-af95-915e880940b8" />

4. If installed correcntly, you should see the `Alation Context` tool listed

![Screenshot 2025-05-05 at 8 08 17 PM](https://github.com/user-attachments/assets/22660586-a9c6-4d99-9c11-54df2011c540)


```text
What certified data sets are related to revenue forecasting?
Find documentation about our customer 360 platform.
List commonly joined tables with order_summary.
```

LibreChat will invoke the MCP tool, which will forward the context API queries to your Alation instance, fetch results, and return them in the chat.

---

## Using Custom Signatures (Optional)

To fine-tune data retrieval, you can embed **signatures** into prompts, just like Claude Desktop.

### Example Signature for Trusted Tables

```json
{
  "table": {
    "fields_required": ["name", "description", "columns"],
    "search_filters": {
      "flags": ["Endorsement"]
    },
    "child_objects": {
      "columns": {
        "fields": ["name", "data_type", "sample_values"]
      }
    }
  }
}
```

Prompt example:

```
Use this signature to search:

{
  "table": {
    "fields_required": ["name", "description", "columns"],
    "search_filters": {
      "flags": ["Endorsement"]
    }
  }
}

What trusted tables exist for financial transactions?
```

---

## Troubleshooting

| Symptom | Solution |
|--------|----------|
| Tool doesn't show in UI | Confirm `mcpServers` is properly defined in `librechat.yaml`, and restart the backend |
| MCP logs show `ModuleNotFoundError` | Ensure you installed the Python package with `pip install -e ".[all]"` in the correct directory |
| Data not fetched correctly | Check Alation credentials (`USER_ID`, `REFRESH_TOKEN`, `ALATION_API_BASE`) |

---

## Docker Deployment Notes for STDIO MCP Servers

### STDIO vs SSE

**LibreChat supports both STDIO and SSE-based MCP servers**, but the `alation_context` tool only supports STDIO mode as of now. This means the MCP server **must run inside the same Docker container** as the LibreChat backend (`api` service), or be mounted into it with the correct path.

---

## Mounting MCP Server Inside LibreChat Container

Update your `docker-compose.override.yaml` file to mount the Python-based Alation MCP server into the LibreChat container:

```yaml
services:
  api:
    volumes:
      - type: bind
        source: ./librechat.yaml
        target: /app/librechat.yaml
      - type: bind
        source: ../alation-mcp-server
        target: /app/mcp-server/alation
```

> Make sure `../alation-mcp-server` is the directory where your Python MCP server (`alation_ai_agent_mcp`) is located.

---

## Notes

- Ensure your `librechat.yaml` references the correct mounted path and tool module
- Validate that all environment variables (`USER_ID`, `REFRESH_TOKEN`, etc.) are correctly set
- Restart LibreChat with `docker compose up -d --build` to apply all changes
