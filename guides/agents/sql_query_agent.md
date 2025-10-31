# sql_query_agent

SQL Query Agent for SQL query generation and analysis.

**Functionality**

This agent specializes in generating, analyzing, and optimizing SQL queries based on natural language descriptions of data needs.
It differs from the Query Flow Agent in that it must be provided a data product.
It will not look for data products to query.  
This is useful if the caller already knows which data product to query and wants an agent which will deterministically query that data product only.

**Input Parameters**

- ` message ` (required, str): Description of the data you need or SQL task
- ` data_product_id ` (required, str): Which data product to use.
- ` chat_id ` (optional, uuid): An existing chat to use. If not provided, a new chat will be created. 

**Returns**

- SQL queries, query analysis, optimization suggestions, and execution guidance.
