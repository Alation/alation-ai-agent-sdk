# check_data_quality

A validation tool that checks data quality for tables or SQL queries using Alation's Data Quality API.

**NOTE** : This BETA feature must be enabled on the Alation instance.

**Functionality**
- Validates data quality for specific tables by table ID
- Analyzes SQL queries for potential data quality issues
- Returns quality scores and detailed quality statements
- Identifies tables below quality threshold
- Supports multiple output formats (JSON or YAML Markdown)

**Input Parameters**
- ` table_ids ` (list, optional): List of table identifiers to check (maximum 30 tables). Use ` alation_context ` to get table IDs first.
- ` sql_query ` (string, optional): SQL query to analyze for quality issues
- ` ds_id ` (int, optional): Data source ID from Alation (required when using ` sql_query ` )
- ` db_uri ` (string, optional): Database URI as alternative to ` ds_id ` (e.g., ` postgresql://@host:port/dbname ` )
- ` output_format ` (string, optional): Response format
- ` "json" ` (default) or ` "yaml_markdown" ` for compact responses
- ` dq_score_threshold ` (int, optional): Quality threshold from 0-100. Tables below this threshold are flagged. Defaults to 70.
- ` bypassed_dq_sources ` (list, optional): Data quality sources to exclude from analysis
- ` default_schema_name ` (string, optional): Default schema name for query parsing

**Valid Parameter Combinations**
1. ` table_ids ` alone
  - Check quality for specific tables
2. ` sql_query ` + ` ds_id `
  - Validate SQL query with data source ID (recommended)
3. ` sql_query ` + ` db_uri `
  - Validate SQL query with database URI (when ds_id is unknown)

**Returns**
- JSON-formatted response (default) or YAML Markdown string containing:
  - Data quality summary with overall scores
  - Item-level quality statements for each table or query element
  - List of tables below the quality threshold
  - Detailed quality metrics and recommendations
