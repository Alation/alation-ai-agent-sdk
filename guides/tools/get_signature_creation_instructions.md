# get_signature_creation_instructions

A helper tool that provides comprehensive instructions for building API signatures.

**Functionality**

This tool provides a markdown formatted document that can be given to an Agent or LLM.
This tool should be used in tandem with the alation_context and bulk_retreival tools.  
Agents should call this tool themselves if they need to use the aforementioned tools.

**Input Parameters**

- ` chat_id ` (optional, uuid): An existing chat to use. If not provided, a new chat will be created. 

**Returns**

Complete instruction set with object types, fields, filters, and examples
