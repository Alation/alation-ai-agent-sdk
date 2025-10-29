# lineage

A lineage retrieval tool to identify upstream or downstream objects relative to the starting object. Supports Column level lineage.

**NOTE** : This BETA feature must be enabled on the Alation instance. Please contact Alation support to do this. Additionally, the lineage tool within the SDK must be explicitly enabled.

**Functionality**

- Access the object's upstream or downstream lineage.
- Graph is filterable by object type.
- Helpful for root cause and impact analysis
- Enables custom field value propagation

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
