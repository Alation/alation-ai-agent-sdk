# custom_agent

Execute a custom agent configuration by its UUID.

**Functionality**

Use this to invoke an agent that has been created in the Alation Agent Studio.
The input, output, and behavior will all depend on the Agent itself, consult the relevant agent's configuration or system prompt for details.
Do not use this to invoke built-in agents, instead execute the agent themselves.

**Usage**

Note: The payload structure depends on the input schema defined for each specific
agent configuration. Consult the agent's documentation for required fields.

```python
custom_agent(agent_config_id="custom-uuid",
             payload={"query": "specific request", "context": {...}})
```

**Parameters**

- ` agent_config_id ` (required, str): The UUID of the agent configuration to use
- ` payload ` (required, Dict[str, Any]): The payload to send to the agent. Must conform to the agent's specific input JSON schema. By default, this will be `{"message": "your question"}` for most conversational agents. More complex agents may accept more parameters, or may not even require a message field at all. Consult your agent configuration before using.
- ` chat_id ` (optional, uuid): An existing chat to use. If not provided, a new chat will be created. 

**Returns**

Dependant on the agent configuration.
