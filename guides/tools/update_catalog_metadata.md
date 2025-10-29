# update_catalog_metadata

A tool to updates metadata for Alation catalog assets by modifying existing objects.

**Supported object types**

- ` glossary_term ` : Individual glossary terms (corresponds to document objects)
- ` glossary_v3 ` : Glossary collections (corresponds to doc-folder objects, i.e., Document Hubs)

**Functionality**

- Creates an async job that updates one or more object field values.

**Input Parameters**

- A list of objects to be updated which include the ` id ` , ` otype ` , ` field_id ` , and the new ` value ` .

**Returns**

- validation error (dict) A dictionary containing a "error" value.
- on success (dict) A dictionary containing a "job_id" value.
