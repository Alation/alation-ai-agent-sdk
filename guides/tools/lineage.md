# Lineage Tool

> The Lineage tool is currently in Beta as is the Bulk Lineage API the tool depends on. Both must be enabled to make use of this capability.

## Background

Accessing enterprise data flows are critical to success with operations and compliance. Whether tracking at the column level or analyzing impact, lineage plays a key role. And Alation's Lineage tool provides this vital functionality.

## Applications

Lineage by itself is simply a more complete picture. Where it shines is in the combination of other tools. In particular it marries well with the following tools:

- Aggregated Context tool
- Data Quality tool
- Data Dictionary tool

## Examples

### Locate the source an upstream data quality issue

Consider a case where a flurry of alerts are sent due to a data quality issue. With multiple issues detected, where do you start? Which one is the real issue?

Leverage the lineage tool to get upstream objects. Then instruct the LLM to fetch data quality for each one. If they converge on a single table or ETL job you now know what to focus on.

### Alert downstream Stewards

Now that we know an issue exists we should alert anyone who relies on those objects.

Use the lineage tool to get downstream objects. Filter them down to affected `bi_report` objects. Call the Aggregated Context tool to return Stewards, (or an Owner custom field). Now we know who to talk with.

### Propagate a custom field value to downstream objects

Imagine a scenario we need to establish wether a column contains PII or not. Our classifier indicates it does not and we've done some spot checks to be sure. It's straight forward to visit the column object in the catalog and change the custom field to not PII.

At the same time we know there are other tables that use columns derived from these values.

Let's put the lineage tool on the job to find other downstream columns. Once we have those we can ask the LLM to update the same field across all the objects. Then use the data dictionary tool to generate a CSV for propagating the new value to each object.