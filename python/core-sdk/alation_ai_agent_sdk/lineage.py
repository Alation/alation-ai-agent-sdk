from typing import List, Literal, Optional, Union
from typing_extensions import TypedDict

class LineageDesignTimeOptions:
    ONLY_DESIGN_TIME = 1
    ONLY_RUN_TIME = 2
    EITHER_DESIGN_OR_RUN_TIME = 3

class LineageDirectionOptions:
    UPSTREAM = 'upstream'
    DOWNSTREAM = 'downstream'

class LineageGraphProcessingOptions:
    CHUNKED = 'chunked'
    COMPLETE = 'complete'

class LineageRootNode(TypedDict):
    id: Union[str, int]
    otype: str

class LineagePagination(TypedDict):
    cursor: int
    batch_size: int
    has_more: bool
    request_id: str


LineageDirectionType = Literal["upstream", "downstream"]
LineageExcludedSchemaIdsType = List[int]
LineageTimestampType = str
LineageKeyTypeType = Literal["id", "fully_qualified_name"]
LineageDesignTimeType = Literal[1, 2, 3]
LineageOTypeFilterType = Optional[List[str]]
LineageGraphProcessingType = Literal['chunked', 'complete']
LineageBatchSizeType = int

LineageResponseRequestIdType = str

class LineageResponseGraphNeighborNode(TypedDict):
    id: Union[str, int]
    otype: str
    # These keys may not be present in all nodes. Please use obj.get() to access them safely.
    fully_qualified_name: str
    is_external: bool
    is_temp: bool

class LineageResponseGraphNode(TypedDict):
    id: Union[str, int]
    otype: str
    # These keys may not be present in all nodes. Please use obj.get() to access them safely.
    fully_qualified_name: str
    is_external: bool
    is_temp: bool
    neighbors: List[LineageResponseGraphNeighborNode]

class LineageToolResponse(TypedDict):
    graph: List[LineageResponseGraphNode]
    direction: LineageDirectionType
    pagination: Optional[LineagePagination]


def make_lineage_kwargs(
    root_node: LineageRootNode,
    processing_mode: Optional[LineageGraphProcessingType] = None,
    show_temporal_objects: Optional[bool] = False,
    design_time: Optional[LineageDesignTimeType] = None,
    max_depth: Optional[int] = 10,
    excluded_schema_ids: Optional[LineageExcludedSchemaIdsType] = None,
    allowed_otypes: Optional[LineageOTypeFilterType] = None,
    time_from: Optional[LineageTimestampType] = None,
    time_to: Optional[LineageTimestampType] = None,
):
    """
    Prepare the keyword arguments for the lineage API call.

    Args:
        root_node (LineageRootNode): The root node for the lineage query.
        processing_mode (Optional[LineageGraphProcessingType]): The processing mode for the query.
        show_temporal_objects (Optional[bool]): Whether to show temporal objects.
        design_time (Optional[LineageDesignTimeType]): The design time option.
        max_depth (Optional[int]): The maximum depth for the query.
        excluded_schema_ids (Optional[LineageExcludedSchemaIdsType]): The excluded schema IDs.
        allowed_otypes (Optional[LineageOTypeFilterType]): The allowed object types.
        time_from (Optional[LineageTimestampType]): The start time for the query.
        time_to (Optional[LineageTimestampType]): The end time for the query.

    Returns:
        dict: The keyword arguments for the lineage API call.
    """

    if processing_mode is None:
        # This is much simpler for the LLM to understand
        processing_mode = LineageGraphProcessingOptions.COMPLETE

    if show_temporal_objects is None:
        show_temporal_objects = False

    if design_time is None:
        design_time = LineageDesignTimeOptions.EITHER_DESIGN_OR_RUN_TIME

    if excluded_schema_ids is None:
        excluded_schema_ids = []

    if time_from is None:
        time_from = ""

    if time_to is None:
        time_to = ""

    key_type = "fully_qualified_name" if isinstance(root_node.get("id"), str) and '.' in root_node.get("id") else "id"
    return {
        "processing_mode": processing_mode,
        "show_temporal_objects": show_temporal_objects,
        "design_time": design_time,
        "max_depth": max_depth,
        "excluded_schema_ids": excluded_schema_ids,
        "allowed_otypes": allowed_otypes,
        "time_from": time_from,
        "time_to": time_to,
        "key_type": key_type,
    }
