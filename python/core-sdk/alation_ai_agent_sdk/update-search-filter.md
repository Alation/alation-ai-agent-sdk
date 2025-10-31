Objective: Update the following tools (`BiReportSearchTool`, `SearchCatalogTool`) and their api functions (`search_bi_reports_stream`, `search_catalog_tool_stream` to accept the `filters` parameter.

Resources:
- Model the `filters` parameter according to `#/components/schemas/Filter` in @../../alation-ai/binding/openapi.json (warning: the file is large)
- Tool class can be found in @core-sdk/alation_ai_agent_sdk/tools.py
- API functions can be found in @core-sdk/alation_ai_agent_sdk/api.py

Steps:
- Ensure each tool's `run` method accepts the `filters` parameter and it is typehinted correctly
- While the parameter is optional, if it is provided it must include `filter_id` and `filter_values` per the openapi spec.
- Ensure the documentation for each tool class and api function describe this parameter accurately
- If either the `run` method's call signature has changed, or if the api function's call signature has changed, we need to update the @dist-langchain and @dist-mcp accordingly.