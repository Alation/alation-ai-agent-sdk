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
- A valid refresh token created from your user account in Alation ([instructions](https://developer.alation.com/dev/docs/authentication-into-alation-apis#create-a-refresh-token-via-the-ui))

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
```

## Running the Example

```bash
python basic_usage.py
```
