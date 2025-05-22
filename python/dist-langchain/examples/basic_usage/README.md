# LangChain Basic Usage Example

This example demonstrates how to create a basic LangChain agent that integrates with the [Alation AI Agent SDK](https://github.com/Alation/alation-ai-agent-sdk) and uses OpenAI's GPT models to query Alation. The agent processes natural language questions and returns structured responses based on metadata from the Alation Data Catalog.

## Requirements

- Python 3.10 or higher
- Access to an Alation Data Catalog instance
- A valid refresh token or client_id and secret. For more details, refer to the [Authentication Guide](https://github.com/Alation/alation-ai-agent-sdk/blob/main/guides/authentication.md).
- OpenAI API key

Install all dependencies with:

```bash
pip install -r requirements.txt
```

## Setup

### Step 1: Environment Variables
Before running the agent, set the following environment variables with your credentials:
```
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

### Step 2: Run the Example Script
```
python usage.py
```

See [usage.py](./usage.py)
