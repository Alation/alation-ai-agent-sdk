# Claude Desktop Integration - Alation MCP Server

This guide explains how to set up and use the Alation Model Context Protocol (MCP) server with Claude Desktop, allowing you to access Alation metadata and catalog information directly within your Claude conversations.

## Prerequisites

- [Claude Desktop](https://claude.ai/download) application installed (macOS or Windows)
- Python 3.10 or higher
- Access to an Alation instance with valid credentials

## Installation

### Step 1: Clone the Repository (TODO: pip install when we have package published)

Clone the repository to your local machine:

```bash
git clone https://github.com/Alation/ai-agent-sdk.git
cd ai-agent-sdk
```

### Step 2: Create and Activate a Virtual Environment

Create and activate a Python virtual environment to isolate your dependencies:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### Step 3: Install the Package with All Dependencies

Install the package in development mode with all required dependencies:

```bash
# Navigate to the python directory if necessary
cd python

# Install with all dependencies
pip install pdm
cd dist-mcp
pdm install
```

### Step 4: Configure Claude Desktop

1. Open Claude Desktop and click on the Claude menu in the top menu bar
2. Select "Settings..."
3. Click on "Developer" in the left navigation
4. Click on "Edit Config" to open the configuration file

This will create or open the configuration file at:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

### Step 5: Add the Alation MCP Server Configuration

Add the following configuration to your `claude_desktop_config.json` file:

```json
{
  "mcpServers": {
    "alation": {
      "command": "/full/path/to/python",
      "args": [
        "-m",
        "alation_ai_agent_mcp"
      ],
      "env": {
        "ALATION_BASE_URL": "https://your-alation-instance.com",
        "ALATION_USER_ID": "123456",
        "ALATION_REFRESH_TOKEN": "your-refresh-token"
      }
    }
  }
}
```

**Important Notes:**
- Replace `/full/path/to/python` with the absolute path to your Python executable
  - On macOS/Linux: Find it with `which python` (while your virtual environment is activated)
  - On Windows: Find it with `where python` (while your virtual environment is activated)
- Replace the Alation variables with your actual values:
  - `https://your-alation-instance.com` with your actual Alation instance URL
  - `123456` with your numeric Alation user ID
  - `your-refresh-token` with your Alation refresh token

### Step 6: Save and Restart Claude Desktop

1. Save the configuration file
2. Completely close Claude Desktop
3. Relaunch the application

## Verifying the Connection

After restarting Claude Desktop, you should see a hammer icon (🔨) in the bottom right corner of the input box. This indicates MCP tools are available.

1. Click on the hammer icon to see available tools
2. You should see the "alation_context" tool listed

If you don't see this icon, check Claude Desktop logs for errors and verify your configuration.

## Using the Alation Tools in Claude

You can now ask Claude questions about your Alation catalog. Examples:

- "What are the commonly joined tables with customer_profile?"
- "Find recent documentation about our data warehouse"
- "Can you explain the difference between loan type and loan term?"
- "What certified data set is used to make decisions on providing credit for customers?"
- "Show me financial reporting datasets and related queries"

When needed, Claude will use the Alation MCP tools to retrieve contextual information and will request your permission before executing tool calls.

## Using Signatures with Claude Desktop

The Alation AI Agent SDK supports customizing data retrieval through signatures. For detailed documentation on signature format and capabilities, see [Using Signatures](../signature.md).

### Example 1: Simple Usage with Claude

When asking Claude questions about your data catalog, you can provide a custom signature in your prompt:

```
Please use this signature when searching:

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

What tables do we have on claims? Fetch from alation.
```

This way, Claude will include this signature when making calls to the Alation context tool, ensuring you receive precisely the information you need, focused on trusted data sources with complete column details.

### Example 2: Using a Default Signature for All Queries

If you want Claude to always use a specific signature for all Alation-related queries in your conversation, you can specify this at the beginning:

For all Alation queries in this conversation, always use the following signature:
```json
{
  "table": {
    "fields_required": ["name", "description", "url"],
    "fields_optional": ["common_joins", "common_filters", "columns"],
    "search_filters": {
      "domain_ids": [42]  // Finance domain
    },
    "child_objects": {
      "columns": {
        "fields": ["name", "data_type", "description"]
      }
    }
  },
  "documentation": {
    "fields_required": ["title", "content", "url"],
    "search_filters": {
      "domain_ids": [42]  // Finance domain
    }
  }
}
```
Now, let's explore our financial data. What tables do we have related to revenue forecasting?

By specifying "always use" at the beginning, you establish a default signature that Claude will apply to all subsequent Alation queries in your conversation. This signature focuses on the finance domain (domain_id 42) and includes both table and documentation objects.

### Example 3: Providing Multiple Signatures for Different Query Types

For more complex scenarios, you can provide multiple signatures and let Claude select the most appropriate one based on your question:

I'm going to ask you questions about our data catalog. Please use the following signatures based on the type of question:

```json
For questions about table structure or data exploration:
{
  "table": {
    "fields_required": ["name", "description", "columns"],
    "child_objects": {
      "columns": {
        "fields": ["name", "data_type", "sample_values"]
      }
    }
  }
}

For questions about documentation or policies:
{
  "documentation": {
    "fields_required": ["title", "content", "url"]
  }
}
```

First question: What fields are available in our customer table?

In this example, you've provided two different signatures for different types of queries. Claude will analyze your question and apply the most appropriate signature based on the context.
