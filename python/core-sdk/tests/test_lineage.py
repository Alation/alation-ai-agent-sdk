import pytest
from unittest.mock import Mock
from alation_ai_agent_sdk.lineage import (
    LineageDesignTimeOptions,
    LineageGraphProcessingOptions,
    make_lineage_kwargs,
)
from alation_ai_agent_sdk.lineage_filtering import (
    get_node_object_key,
    get_initial_graph_state,
    resolve_neighbors,
    filter_graph,
    build_filtered_graph,
)
from alation_ai_agent_sdk.tools import AlationLineageTool
from alation_ai_agent_sdk.api import AlationAPIError


def test_make_lineage_kwargs_creates_defaults():
    response = make_lineage_kwargs(root_node={"id": 1, "otype": "table"})
    assert response["processing_mode"] == LineageGraphProcessingOptions.COMPLETE
    assert not response["show_temporal_objects"]
    assert response["design_time"] == LineageDesignTimeOptions.EITHER_DESIGN_OR_RUN_TIME
    assert response["max_depth"] == 10
    assert response["excluded_schema_ids"] == []
    assert response["time_from"] == ""
    assert response["time_to"] == ""
    assert response["key_type"] == "id"


def test_make_lineage_kwargs_recognizes_fully_qualified_name_as_key_type():
    response = make_lineage_kwargs(
        root_node={"id": "1.my_schema.my_table", "otype": "table"}
    )
    assert response["key_type"] == "fully_qualified_name"


def test_make_lineage_kwargs_respects_provided_values():
    expected_max_depth = 22
    expected_excluded_schema_ids = [1, 2]
    expected_allowed_otypes = ["table"]
    expected_processing_mode = LineageGraphProcessingOptions.CHUNKED
    expected_design_time = LineageDesignTimeOptions.ONLY_DESIGN_TIME
    response = make_lineage_kwargs(
        root_node={"id": 1, "otype": "table"},
        max_depth=expected_max_depth,
        excluded_schema_ids=expected_excluded_schema_ids,
        allowed_otypes=expected_allowed_otypes,
        processing_mode=expected_processing_mode,
        design_time=expected_design_time,
    )
    assert response["max_depth"] == expected_max_depth
    assert response["excluded_schema_ids"] == expected_excluded_schema_ids
    assert response["allowed_otypes"] == expected_allowed_otypes
    assert response["processing_mode"] == expected_processing_mode
    assert response["design_time"] == expected_design_time


def test_get_node_object_key():
    response = get_node_object_key({"id": 1, "otype": "table"})
    assert response == "table:1"


def test_get_initial_graph_state():
    graph_nodes_from_response = [
        {"id": 1, "otype": "table", "neighbors": [{"id": 2, "otype": "table"}]},
        {"id": 2, "otype": "table"},
    ]
    expected_ordered_keys = [
        get_node_object_key(graph_nodes_from_response[0]),
        get_node_object_key(graph_nodes_from_response[1]),
    ]
    ordered_keys, key_to_node, visited = get_initial_graph_state(
        graph_nodes_from_response
    )
    assert expected_ordered_keys == ordered_keys
    assert len(key_to_node) == 2
    node1_obj_key = get_node_object_key(graph_nodes_from_response[0])
    node2_obj_key = get_node_object_key(graph_nodes_from_response[1])
    assert node1_obj_key in key_to_node
    assert node2_obj_key in key_to_node
    assert key_to_node[node1_obj_key] == graph_nodes_from_response[0]
    assert key_to_node[node2_obj_key] == graph_nodes_from_response[1]
    assert visited is not None
    assert len(visited) == 0
    assert isinstance(visited, dict)


def test_resolve_neighbors_unvisited_allowed_node_no_neighbors():
    node = {"id": 1, "otype": "table"}
    node_key = get_node_object_key(node)
    visited = {}
    key_to_node = {
        node_key: node,
    }
    descendant_nodes, visited = resolve_neighbors(
        node_key=node_key,
        visited=visited,
        key_to_node=key_to_node,
        allowed_types={"table"},
    )
    assert descendant_nodes == []
    assert visited == {node_key: [node]}


def test_resolve_neighbors_unvisited_omitted_node_no_neighbors():
    node = {"id": 1, "otype": "dataflow"}
    node_key = get_node_object_key(node)
    visited = {}
    key_to_node = {
        node_key: node,
    }
    descendant_nodes, visited = resolve_neighbors(
        node_key=node_key,
        visited=visited,
        key_to_node=key_to_node,
        allowed_types={"view"},
    )
    assert descendant_nodes == []
    assert visited == {node_key: []}


def test_resolve_neighbors_unvisited_allowed_node_with_neighbors():
    node2 = {"id": 2, "otype": "table"}
    node1 = {"id": 1, "otype": "table", "neighbors": [node2]}
    node1_key = get_node_object_key(node1)
    node2_key = get_node_object_key(node2)

    visited = {}
    key_to_node = {node1_key: node1, node2_key: node2}
    descendant_nodes, visited = resolve_neighbors(
        node_key=node1_key,
        visited=visited,
        key_to_node=key_to_node,
        allowed_types={"table"},
    )
    assert descendant_nodes == [node1]
    assert visited == {node1_key: [node1], node2_key: [node2]}


def test_resolve_neighbors_unvisited_omitted_node_with_neighbors():
    node2 = {"id": 2, "otype": "table"}
    node1 = {"id": 1, "otype": "dataflow", "neighbors": [node2]}
    node1_key = get_node_object_key(node1)
    node2_key = get_node_object_key(node2)

    visited = {}
    key_to_node = {node1_key: node1, node2_key: node2}
    descendant_nodes, visited = resolve_neighbors(
        node_key=node1_key,
        visited=visited,
        key_to_node=key_to_node,
        allowed_types={"table"},
    )
    assert descendant_nodes == []
    assert visited == {node2_key: [node2], node1_key: []}


def test_resolve_neighbors_visited_allowed_node():
    node = {
        "id": 1,
        "otype": "table",
    }
    node_key = get_node_object_key(node)
    key_to_node = {
        node_key: node,
    }
    orig_visited = {
        node_key: [node],
    }
    descendant_nodes, visited = resolve_neighbors(
        node_key=node_key,
        visited=orig_visited,
        key_to_node=key_to_node,
        allowed_types={"table"},
    )
    assert descendant_nodes == [node]
    assert visited == orig_visited  # Should not change visited state


def test_resolve_neighbors_visited_omitted_node():
    node = {
        "id": 1,
        "otype": "dataflow",
    }
    node_key = get_node_object_key(node)
    key_to_node = {
        node_key: node,
    }
    orig_visited = {
        node_key: [],
    }
    descendant_nodes, visited = resolve_neighbors(
        node_key=node_key,
        visited=orig_visited,
        key_to_node=key_to_node,
        allowed_types={"table"},
    )
    assert descendant_nodes == []
    assert visited == orig_visited  # Should not change visited state


def test_filter_graph_basic():
    graph_nodes = [
        {
            "id": 1,
            "otype": "table",
            "neighbors": [{"id": 2, "otype": "table"}, {"id": 3, "otype": "dataflow"}],
        },
        {"id": 2, "otype": "table"},
        {"id": 3, "otype": "dataflow"},
    ]
    allowed_types = {"table"}
    filtered_graph = filter_graph(nodes=graph_nodes, allowed_types=allowed_types)
    assert len(filtered_graph) == 2  # Only table nodes should remain
    assert all(node["otype"] == "table" for node in filtered_graph)
    assert filtered_graph[0]["id"] == 1
    assert filtered_graph[1]["id"] == 2


def test_filter_graph_nested():
    graph_nodes = [
        {
            "id": 1,
            "otype": "table",
            "fully_qualified_name": "1",
            "neighbors": [{"id": 2, "otype": "table", "fully_qualified_name": "2"}],
        },
        {
            "id": 2,
            "otype": "table",
            "fully_qualified_name": "2",
            "neighbors": [
                {"id": 3, "otype": "etl", "fully_qualified_name": "3"},
                {"id": 4, "otype": "table", "fully_qualified_name": "4"},
            ],
        },
        {
            "id": 3,
            "otype": "etl",
            "fully_qualified_name": "3",
            "neighbors": [{"id": 5, "otype": "table", "fully_qualified_name": "5"}],
        },
        {"id": 4, "otype": "table", "fully_qualified_name": "4", "neighbors": []},
        {"id": 5, "otype": "table", "fully_qualified_name": "5", "neighbors": []},
        {
            "id": 6,
            "otype": "table",
            "fully_qualified_name": "6",
            "neighbors": [{"id": 3, "otype": "etl", "fully_qualified_name": "3"}],
        },
        {
            "id": 7,
            "otype": "etl",
            "fully_qualified_name": "7",
            "neighbors": [{"id": 8, "otype": "etl", "fully_qualified_name": "8"}],
        },
        {"id": 8, "otype": "etl", "fully_qualified_name": "8", "neighbors": []},
        {
            "id": 9,
            "otype": "etl",
            "fully_qualified_name": "9",
            "neighbors": [{"id": 10, "otype": "table", "fully_qualified_name": "10"}],
        },
        {"id": 10, "otype": "table", "fully_qualified_name": "10", "neighbors": []},
    ]
    allowed_types = {"table"}
    filtered_graph = filter_graph(nodes=graph_nodes, allowed_types=allowed_types)
    assert len(filtered_graph) == 6  # Only table nodes should remain
    assert all(node["otype"] == "table" for node in filtered_graph)
    assert filtered_graph[0]["id"] == graph_nodes[0]["id"]
    assert filtered_graph[1]["id"] == graph_nodes[1]["id"]
    assert filtered_graph[2]["id"] == graph_nodes[3]["id"]
    assert filtered_graph[3]["id"] == graph_nodes[4]["id"]
    assert filtered_graph[4]["id"] == graph_nodes[5]["id"]
    assert filtered_graph[5]["id"] == graph_nodes[9]["id"]


def test_build_filtered_graph():
    ordered_keys = ["table:1", "table:2", "dataflow:3", "fake_type:5"]
    kept_keys = {"table:1", "table:2"}
    key_to_node = {
        "table:1": {
            "id": 1,
            "otype": "table",
            "neighbors": [
                {
                    "id": 2,
                    "otype": "table",
                    "neighbors": [{"id": 4, "otype": "throw_away"}],
                }
            ],
        },
        "table:2": {"id": 2, "otype": "table"},
        "dataflow:3": {"id": 3, "otype": "dataflow"},
    }
    filtered_graph = build_filtered_graph(ordered_keys, kept_keys, key_to_node)
    assert len(filtered_graph) == 2
    assert filtered_graph[0]["id"] == 1
    assert filtered_graph[0]["otype"] == "table"
    assert filtered_graph[0]["neighbors"] == [{"id": 2, "otype": "table"}]
    assert filtered_graph[1]["id"] == 2
    assert filtered_graph[1]["otype"] == "table"
    assert filtered_graph[1]["neighbors"] == []


@pytest.fixture
def mock_api():
    """Creates a mock AlationAPI for testing."""
    api = Mock()
    api.enable_streaming = False
    return api


@pytest.fixture
def get_lineage_tool(mock_api):
    """Creates an AlationLineageTool with mock API."""
    return AlationLineageTool(mock_api)


def test_alation_lineage_tool_calls_streaming_api(get_lineage_tool, mock_api):
    """Test that the tool calls the streaming API method."""
    # Mock response from backend
    mock_response = {
        "graph": [
            {
                "id": 1,
                "otype": "table",
                "fully_qualified_name": "db.schema.table1",
                "neighbors": []
            }
        ],
        "direction": "downstream",
        "pagination": None
    }

    # Mock the streaming method to return a generator
    def mock_generator():
        yield mock_response

    mock_api.alation_lineage_stream.return_value = mock_generator()

    result = get_lineage_tool.run(
        root_node={
            "id": 1,
            "otype": "table",
        },
        direction="downstream",
    )

    # Verify API was called
    mock_api.alation_lineage_stream.assert_called_once()

    # Verify result
    assert "graph" in result
    assert "direction" in result
    assert result["direction"] == "downstream"


def test_alation_lineage_tool_returns_api_errors(get_lineage_tool, mock_api):
    """Test that API errors are properly handled and returned."""
    # Mock API error
    api_error = AlationAPIError(
        message="Bad Request",
        status_code=400,
        reason="Bad Request",
        resolution_hint="Check API parameters",
    )
    mock_api.alation_lineage_stream.side_effect = api_error

    result = get_lineage_tool.run(
        root_node={"id": 1, "otype": "table"},
        direction="downstream",
        limit=100,
        batch_size=100,
    )

    # Verify API was called
    mock_api.alation_lineage_stream.assert_called_once()

    # Verify error handling
    assert "error" in result
    assert result["error"]["message"] == "Bad Request"
    assert result["error"]["status_code"] == 400
    assert result["error"]["reason"] == "Bad Request"


def test_filtering_allowed_types_on_incomplete_graph():
    allowed_otypes = {"table"}
    response = {
        "graph": [
            {
                "otype": "table",
                "neighbors": [
                    {
                        "otype": "table",
                        "id": 21854,
                        "fully_qualified_name": "17.uc_production.fdm_prepare.applications",
                    },
                    {
                        "otype": "table",
                        "id": 21866,
                        "fully_qualified_name": "17.uc_production.fdm_prepare.underwriting_variables",
                    },
                ],
                "id": 64850,
                "fully_qualified_name": "17.uc_production.dwh_servicing.payment_funnel",
            }
        ],
        "pagination": {
            "request_id": "0bdd51f98cf245eb936bf7845bae6e2d",
            "cursor": 3,
            "batch_size": 2,
            "has_more": True,
        },
        "direction": "upstream",
    }

    result = filter_graph(response["graph"], allowed_otypes)
    assert len(result) == 1
    assert result[0]["id"] == 64850
    assert result[0]["otype"] == "table"
    assert "neighbors" in result[0]
    assert len(result[0]["neighbors"]) == 2
    for neighbor in result[0]["neighbors"]:
        assert neighbor["otype"] == "table"
