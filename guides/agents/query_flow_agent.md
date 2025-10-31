# query_flow_agent

Query Flow Agent for data product query workflow management.

**Functionality**

This agent leverages existing data products to create, optimize, and execute data source queries.
It is capable of SQL query planning & execution, but is also able to determine the appropriate data sources to used by understanding data products.
This can be useful if the caller wants to query data, but does not know what low level tables or warehouses to use.

**Input Parameters**

- ` message ` (required, str): Description of your query workflow needs.
- ` chat_id ` (optional, uuid): An existing chat to use. If not provided, a new chat will be created. 

**Returns**

- Query workflow guidance, optimization suggestions, execution plans, and query output.
