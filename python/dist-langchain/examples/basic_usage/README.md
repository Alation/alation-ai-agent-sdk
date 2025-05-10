# LangChain Basic Usage Example

This example demonstrates how to create a basic LangChain agent that integrates with the [Alation AI Agent SDK](https://github.com/Alation/ai-agent-sdk) and uses OpenAI's GPT models to query Alation’s metadata catalog. The agent processes natural language questions and returns structured responses based on metadata from the Alation catalog.

## Requirements

- Python 3.10+
- Access to:
  - Alation Data Catalog
  - OpenAI API

Install all dependencies with:

```bash
pip install -r requirements.txt
```

## Setup

### Step 1: Environment Variables
Before running the agent, set the following environment variables with your credentials:
```
export ALATION_BASE_URL="https://your-alation-instance.com"
export ALATION_USER_ID="your_alation_user_id"
export ALATION_REFRESH_TOKEN="your_refresh_token"
export OPENAI_API_KEY="your_openai_api_key"
```

### Step 2: Run the Example Script
```
python usage.py
```

See [usage.py](./usage.py)
