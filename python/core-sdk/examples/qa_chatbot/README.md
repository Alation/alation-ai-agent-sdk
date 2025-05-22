# Alation AI Agent SDK - QA Chatbot

This example demonstrates how to build a question-answering chatbot that uses the Alation AI Agent SDK to access metadata from the Alation Data Catalog.

## Overview

The example shows how to:

- Use the Alation SDK to retrieve contextual information from the catalog
- Integrate with OpenAI's GPT models for natural language understanding
- Create effective signatures for dynamic field selection
- Maintain conversation context through multiple interactions

## Prerequisites

- Python 3.10 or higher
- Access to an Alation Data Catalog instance
- A valid refresh token or client_id and secret. For more details, refer to the [Authentication Guide](https://github.com/Alation/alation-ai-agent-sdk/blob/main/guides/authentication.md).
- OpenAI API key

## Setup

1. Install the required packages:

```bash
pip install -r requirements.txt
```

2. Set up your environment variables:

```bash
export ALATION_BASE_URL="https://your-alation-instance.com"
export ALATION_AUTH_METHOD="user_account"  # or "service_account"

# For user account authentication
export ALATION_USER_ID="your-user-id"
export ALATION_REFRESH_TOKEN="your-refresh-token"

# For service account authentication
export ALATION_CLIENT_ID="your-client-id"
export ALATION_CLIENT_SECRET="your-client-secret"

export OPENAI_API_KEY="your_openai_api_key"
```

## Running the Example

### Interactive Mode

Start an interactive session where you can ask questions about your data catalog:

```bash
python data_catalog_qa.py
```

### Single Question Mode

Ask a specific question directly:

```bash
python data_catalog_qa.py --question "What tables contain customer information?"
```

### Conversation Mode

Enable conversation mode to maintain context between questions:

```bash
python data_catalog_qa.py --conversation
```

## How It Works

1. The user asks a question about the data catalog
2. The chatbot uses the Alation SDK to retrieve relevant metadata
3. The SDK's internal LLM handles query understanding and dynamic field selection
4. GPT-4 generates a natural language answer based on the metadata
5. (Optional) Conversation history is maintained for context-aware follow-up questions

## Key Features

- **Comprehensive Signatures**: Uses both required and optional fields for dynamic field selection
- **Conversation History**: Maintains context across multiple questions
- **Error Handling**: Gracefully handles API errors and missing information

## Example Questions

- "What tables contain customer data?"
- "Tell me about the orders table and its columns"
- "What documentation do we have about data governance?"
- "How does the customers table relate to the orders table?"
- "Can you explain the purpose of the sales_fact table?"