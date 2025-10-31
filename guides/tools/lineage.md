# lineage

A lineage retrieval tool to identify upstream or downstream objects relative to the starting object. Supports Column level lineage.

> [!WARNING]
> This BETA feature must be enabled on the Alation instance.
> Please contact Alation support to do this.
> Additionally, the lineage tool within the SDK must be explicitly enabled.

**Functionality**

This tool allows for traversal of Alation's lineage graph in relation to a given object.
The graph either be for ancestors or descendants of the root object.
If `allowed_otypes` is provided, the resulting graph will be limited to entities of those types.

## Background
Accessing enterprise data flows are critical to success with operations and compliance.
Whether tracking at the column level or analyzing impact, lineage plays a key role. And Alation's Lineage tool provides this vital functionality.

## Applications

Lineage by itself is simply a more complete picture. Where it shines is in the combination of other tools. In particular it marries well with the following tools:

- Aggregated Context tool
- Data Quality tool
- Data Dictionary tool

**Input Parameters**

- ` root_node ` (dict) The starting object. Must contain ` id ` and ` otype ` .
- ` direction ` (upsteam\|downstream) The direction to resolve the lineage graph from.
- ` limit ` (optional int) Defaults to 1,000.
- ` batch_size ` (optional int) Defaults to 1,000.
- ` max_depth ` (optional int) The maximumn depth to transerve of the graph. Defaults to 10.
- ` allowed_otypes ` (optional string\[\]) Controls which types of nodes are allowed in the graph.
- ` pagination ` (optional dict) Contains information about the request including cursor identifier.
- ` show_temporal_objects ` (optional bool) Defaults to false.
- ` design_time ` (optional 1,2,3) 1 for design time objects. 2 for run time objects. 3 for both design and run time objects.
- ` excluded_schema_ids ` (optional int\[\]) Remove nodes if they belong to these schemas.
- ` time_from ` (optional timestamp w/o timezone) Controls the start point of a time period.
- ` time_to ` (optional timestamp w/o timezone) Controls the ending point of a time period.

**Returns**

- (dict) An object containing the lineage graph, the direction, and any pagination values.

## Examples

### Locate the source an upstream data quality issue

Consider a case where a flurry of alerts are sent due to a data quality issue. With multiple issues detected, where do you start? Which one is the real issue?

Leverage the lineage tool to get upstream objects. Then instruct the LLM to fetch data quality for each one. If they converge on a single table or ETL job you now know what to focus on.

### Alert downstream Stewards

Now that we know an issue exists we should alert anyone who relies on those objects.

Use the lineage tool to get downstream objects. Filter them down to affected `bi_report` objects. Call the Aggregated Context tool to return Stewards, (or an Owner custom field). Now we know who to talk with.

### Propagate a custom field value to downstream objects

Imagine a scenario where we need to establish wether a column contains PII or not. Our classifier indicates it does not and we've done some spot checks to be sure. It's straight forward to visit the column object in the catalog and change the custom field to not PII.

At the same time we know there are other tables that use columns derived from these values.

Let's put the lineage tool on the job to find other downstream columns. Once we have those we can ask the LLM to update the same field across all the objects. Then use the data dictionary tool to generate a CSV for propagating the new value to each object.

