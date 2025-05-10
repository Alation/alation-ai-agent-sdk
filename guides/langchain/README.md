# LangChain Integration

This guide introduces integrating the Alation AI Agent SDK with LangChain.

## Overview

The Alation SDK can be used with LangChain to create AI agents that can query your Alation catalog using natural language. This integration allows you to:

- Use Alation metadata in LangChain agents
- Build applications that can answer questions about your data catalog
- Create conversational interfaces for data discovery

## Complete Example

For a full working example, see our [LangChain usage example](../../python/dist-langchain/examples/basic_usage/usage.py).

## Key Components

The integration requires these main components:

1. **SDK Initialization**
   ```python
   sdk = AlationAIAgentSDK(
       base_url=base_url,
       user_id=int(user_id),
       refresh_token=refresh_token
   )
   ```

2. **Tool Creation**
   ```python
   tools = get_langchain_tools(sdk)
   ```

3. **Agent Setup**
   ```python
   agent = create_openai_functions_agent(
      llm=llm,
      tools=tools,
      prompt=prompt
   )
   executor = AgentExecutor(agent=agent, tools=tools)
   ```
   
## Using Signatures with LangChain

The Alation AI Agent SDK supports customizing data retrieval through signatures. For detailed documentation on signature format and capabilities, see [Using Signatures](../signature.md).

### Example Usage with LangChain

```python
# Define a signature to filter for trusted tables
# Note: This example uses flags for trusted tables, but each organization may identify them differently.
signature = {
    "table": {
        "fields_required": ["name", "description", "url"],
        "search_filters": {
            "flags": ["Endorsement"]  # Only return trusted tables
        }
    }
}

# Use it with your agent
response = executor.run({
    "question": "What tables contain customer data?",
    "signature": signature
})
```
