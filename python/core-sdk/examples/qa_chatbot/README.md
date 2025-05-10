# Alation AI Agent SDK - QA Chatbot

This example demonstrates how to build a question-answering chatbot that uses the Alation AI Agent SDK to access metadata from the Alation Data Catalog.

## Overview

The example shows how to:

- Use the Alation SDK to retrieve contextual information from the catalog
- Integrate with OpenAI's GPT models for natural language understanding
- Create effective signatures for dynamic field selection
- Maintain conversation context through multiple interactions

## Prerequisites

- Python 3.10+
- A valid API Access Token created on your Alation Data Catalog instance
- OpenAI API key (for GPT-4)

## Setup

1. Install the required packages:

```bash
pip install -r requirements.txt
```

2. Set up your environment variables:

```bash
export ALATION_BASE_URL="https://your-alation-instance.com"
export ALATION_USER_ID="your_alation_user_id"
export ALATION_REFRESH_TOKEN="your_refresh_token"
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