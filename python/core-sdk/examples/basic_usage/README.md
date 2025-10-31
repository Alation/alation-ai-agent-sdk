# Alation AI Agent SDK - Basic Usage

This example demonstrates the fundamental usage of the Alation AI Agent SDK to interact with the Alation Data Catalog.

## Overview

The example illustrates:

- Initializing the Alation SDK
- Making basic context queries
- Using signatures to customize responses

## Prerequisites

- Python 3.10 or higher
- Access to an Alation Data Catalog instance
- A valid refresh token or client_id and secret. For more details, refer to the [Authentication Guide](https://github.com/Alation/alation-ai-agent-sdk/blob/main/guides/authentication.md).

## Setup

1. Install the required packages:

```bash
pip install -r requirements.txt
```

2. Set up your environment variables:

```bash
export ALATION_BASE_URL="https://your-alation-instance.com"
export ALATION_AUTH_METHOD="service_account"

# For service account authentication
export ALATION_CLIENT_ID="your-client-id"
export ALATION_CLIENT_SECRET="your-client-secret"
```

## Running the Example

```bash
python basic_usage.py
```
