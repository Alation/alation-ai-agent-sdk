# Testing Your Alation MCP Server with Inspector

This guide walks through the process of testing your Alation AI Agent SDK's Model Context Protocol (MCP) server using the MCP Inspector tool.

## Prerequisites

- Python 3.10 or higher
- Node.js installed (for npx)
- Access to an Alation instance

## Step 1: Activate Your Environment

First, activate your Python virtual environment:

```bash
# If using venv or please replace venv with your virtual envt
source /path/to/your/venv/bin/activate
```

Verify your environment is active by checking the prompt - it should show `(venv)` at the beginning.

## Step 2: Set Required Environment Variables

The Alation MCP server requires three environment variables:

```bash
# Set environment variables for your Alation instance
export ALATION_BASE_URL="https://your-alation-instance.com"
export ALATION_USER_ID="123456"  # Your numeric user ID
export ALATION_REFRESH_TOKEN="your-refresh-token"
```

Verify the variables are properly set:

```bash
echo $ALATION_BASE_URL
echo $ALATION_USER_ID
echo $ALATION_REFRESH_TOKEN
```

## Step 3: Run the MCP Server with Inspector

You have two options to run your server with the MCP Inspector:

### Option 1: Using MCP CLI

```bash
# Navigate to your python directory first
cd /path/to/workspace/ai-agent-sdk/python

# Using explicit absolute path
mcp dev /home/username/projects/ai-agent-sdk/python/dist-mcp/alation_ai_agent_mcp/server.py

```

### Option 2: Using NPX

```bash
# Navigate to your python directory first
cd /path/to/workspace/ai-agent-sdk/python

# Run the server with NPX
npx @modelcontextprotocol/inspector python /home/username/projects/ai-agent-sdk/python/dist-mcp/alation_ai_agent_mcp/server.py
```

Either approach will launch the MCP Inspector UI in your browser.

## Step 4: Test with the Inspector UI (TODO: Add a screenshot)

1. Click the "Connect" button in the Inspector UI
2. Once connected, navigate to the "Tools" tab
3. Click "List Tools" to see available tools
4. Select the "alation_context" tool from the list
5. In the right panel, enter your natural language question in the "question" section. 
6. Click "Call Tool" to execute
7. Review the response in the results section below

## Using Signatures with MCP Inspector

The Alation AI Agent SDK supports customizing data retrieval through signatures. For detailed documentation on signature format and capabilities, see [Using Signatures](../signature.md).

### Testing Signatures with MCP Inspector

1. Start the MCP Inspector and connect to your Alation MCP server
2. Navigate to the "Tools" tab and select "alation_context"
3. In the "question" field, enter your natural language query
4. In the "signature" field, paste your JSON signature
5. Click "Call Tool" to execute

Example:
```
#Question:
What tables contain customer data?
```
```
#Signature:
 {
    "table": {
      "fields_required": ["name", "description", "url"],
      "search_filters": {
        "flags": ["Endorsement"]
      }
    }
  }
```

## Troubleshooting

If you encounter issues:

- **Connection errors**: Verify environment variables are set correctly
- **Tool execution failures**: Check Alation instance connectivity
- **Missing dependencies**: Run `pip install -r requirements.txt` to ensure all dependencies are installed
- **Path issues**: Use absolute paths when running commands
