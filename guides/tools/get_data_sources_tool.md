# get_data_sources_tool

Retrieve available data sources from the catalog.

**Functionality**

This tool lists data sources that are available in the Alation catalog.

**Input Parameters**

- ` limit ` (optional, int): Maximum number of data sources to return (default: 100)
- ` chat_id ` (optional, uuid): An existing chat to use. If not provided, a new chat will be created. 

**Returns**

- List of available data sources along with their title and URL.
