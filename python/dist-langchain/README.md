# Langchain Integration

This package integrates the Alation AI Agent SDK with the Langchain framework, allowing Langchain agents to leverage metadata from the Alation Data Catalog.

## Overview

The Langchain integration enables:

- Using Alation's context tool within Langchain agent workflows
- Accessing Alation metadata through Langchain's structured tools interface
- Building sophisticated AI agents that can reason about your data catalog

## Installation

```bash
pip install alation-ai-agent-langchain
```

## Prerequisites

- Python 3.10 or higher
- Access to an Alation Data Catalog instance

## Quick Start

```python
import os
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from alation_ai_agent_sdk import AlationAIAgentSDK
from alation_ai_agent_langchain import get_langchain_tools

# Initialize Alation SDK
sdk = AlationAIAgentSDK(
    base_url=os.getenv("ALATION_BASE_URL"),
    user_id=int(os.getenv("ALATION_USER_ID")),
    refresh_token=os.getenv("ALATION_REFRESH_TOKEN")
)

# Get Langchain tools
tools = get_langchain_tools(sdk)

# Define agent prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant using Alation's metadata catalog."),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Initialize LLM and create agent
llm = ChatOpenAI(model="gpt-4o", temperature=0)
agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)

# Create agent executor
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Run the agent
response = executor.invoke({
  "input": "What tables contain customer data?"}
)
print(response)
```

## Using Signatures with Langchain

You can pass Alation signatures through the Langchain agent:

```python
# Define a signature to customize the response
tables_only_signature = {
  "table": {
    "fields_required": ["name", "title", "description", "url"]
  }
}

# Pass the signature with the input
response = executor.invoke({
    "input": "What tables contain sales data?",
    "signature": tables_only_signature,
})
print(response)
```


See the [examples directory](https://github.com/Alation/alation-ai-agent-sdk/tree/main/python/dist-langchain/examples/) for a complete example of a return eligibility agent built with Langchain and Alation.