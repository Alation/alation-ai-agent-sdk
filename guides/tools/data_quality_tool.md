# Data Quality Tool

## Background

Agents specializing in Data Analyst capabilities are democratizing access to data. These days it's not uncommon to have users or agents running arbitrary SQL queries. This makes the promise of data driven decisions a reality but not without risk. Decisions based on incorrect or incomplete data represent a threat to organizations.

Alation can mitigate these outcomes by surfacing data quality concerns.

## Applications

Use the data quality tool to summarize knowledge from several data quality sources. The tool aggregates data across trust flags as well as open and native data quality. This data quality classification helps LLMs assess how to qualify query results.

When invoked before query execution this pre-flight check can deflect problematic queries. Deflection improves response latency and saves compute cost.  It offers a chance to rewrite queries avoiding bad tables.

Furthermore, it calls into question any analysis which depends on tables of concern. This is a powerful tool when applied to notebooks or dashboards.

## Responses

The data quality tool's response contains two things. First it contains individual tables grouped by their data quality status. Second it includes an data quality summary for the entire request.

It support a yaml / markdown mode for more compact responses which saves tokens.

## Data Quality Summaries

Data quality summaries fall into three buckets: low, high, and unknown.

Low data quality indicates negative results from at least one data quality source. High data quality only exists with positive data quality checks and no warnings. Everything else falls into the unknown bucket.

### One bad apple

The data quality summary follows a one bad apple principle. For instance, imagine a SQL query that joins two tables. One of those tables is deprecated. The summary for that query would be low data quality. Additionally the response will identify which table was responsible.

### Unknowable

We add warnings any time a referenced table cannot be resolved within the tool. It could be they aren't part of the data catalog. Perhaps they were never added or removed at some point. Or table names may not be fully qualified entities. Likewise certain tables are only visible to specific users.

We classify responses as unknown if there are no results to draw conclusions from. And even with many positive results a single unresolvable table is all it takes for the unknown status.

To recap here are a few concrete examples:

#### Low data quality
- One negative data quality item 
- Ten positive data quality items + one negative data quality item
- Two data quality warnings + two negative data quality items

#### Unknown data quality
- Two data quality warnings
- Ten positive data quality items + one data quality warning

#### High data quality
- One or more positive data quality items


## Examples

### Analyzing a SQL Query

The data query tool may by used to classify an individual SQL query. It does this by resolving the mentioned tables to catalog objects and their data quality.

As part of table resolution we need a reference to the data source. A `ds_id` or a `db_uri` is mandatory to ensure we can locate the correct table. And knowing the data source means we can parse the SQL query using the appropriate SQL dialect.

The `db_id` parameter is unambiguous and strongly recommended. If that isn't feasible the `db_uri` parameter may be used instead.

### Analyzing `table_ids`

Additionally, the tool supports using a list of table ids. This bypasses the SQL query parsing and goes straight to resolving data quality.

The tool supports a maximum of 30 table ids at a time. It's important to note there is only a single data quality summary for each request.

### Bypassing one or more data quality sources

It's possible to opt-out of using specific data quality sources.  If you aren't using open data quality or Alation's native data quality product you can bypass them. Similarly, you can skip trust flags if you don't care about deprecated objects.

To achieve this ask the LLM to bypass them in either your chat prompt or within your agent's system prompt.