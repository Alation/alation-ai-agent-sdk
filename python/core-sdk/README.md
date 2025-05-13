# Alation AI Agent SDK

The Alation AI Agent SDK is a Python library that enables AI agents to access and leverage metadata from the Alation Data Catalog.

## Overview

This SDK provides a simple, programmatic way for AI applications to:

- Retrieve contextual information from the Alation catalog
- Use natural language questions to search for relevant metadata
- Customize response formats using signature specifications

## Installation

```bash
pip install alation-ai-agent-sdk
```

## Prerequisites

To use the SDK, you'll need:

- Python 3.10 or higher
- A valid API Access Token created on your Alation Data Catalog instance

## Quick Start

```python
from alation_ai_agent_sdk import AlationAIAgentSDK

# Initialize the SDK with your credentials
sdk = AlationAIAgentSDK(
    base_url="https://your-alation-instance.com",
    user_id=12345,
    refresh_token="your-refresh-token"
)

# Ask a question about your data
response = sdk.get_context(
    "What tables contain sales information?"
)
print(response)

# Use a signature to customize the response format
signature = {
    "table": {
        "fields_required": ["name", "title", "description"]
        }
    }

response = sdk.get_context(
    "What are the customer tables?",
    signature
)
print(response)
```


## Core Features

### Response Customization with Signatures

You can customize the data returned by the Alation context tool using signatures:

```python
# Only include specific fields for tables
table_signature = {
    "table": {
        "fields_required": ["name", "description", "url"]
    }
}

response = sdk.get_context(
    "What are our fact tables?",
    table_signature
)
```

For detailed documentation on signature format and capabilities, see [Using Signatures](https://github.com/Alation/alation-ai-agent-sdk/tree/main/guides/signature.md).
### Getting Available Tools


```python
# Get all available tools
tools = sdk.get_tools()
```
