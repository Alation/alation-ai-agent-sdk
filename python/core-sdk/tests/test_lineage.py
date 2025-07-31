import pytest
from unittest.mock import (
    MagicMock,
    Mock,
    patch,
)
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
from alation_ai_agent_sdk.api import (
    AlationAPI,
    AlationAPIError,
    UserAccountAuthParams,
)
from .test_sdk import (
    REFRESH_TOKEN_RESPONSE_SUCCESS,
    JWT_RESPONSE_SUCCESS,
    mock_requests_post,
    mock_requests_get,
)

def test_make_lineage_kwargs_creates_defaults():
    response = make_lineage_kwargs(
      root_node={"id": 1, "otype": "table"}
    )
    assert response["processing_mode"] == LineageGraphProcessingOptions.COMPLETE
    assert response["show_temporal_objects"] == False
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
      design_time=expected_design_time
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
        {
            "id": 1,
            "otype": "table",
            "neighbors": [
                {
                    "id": 2,
                    "otype": "table"
                }
            ]
        },
        {
            "id": 2,
            "otype": "table"
        }
    ]
    expected_ordered_keys = [get_node_object_key(graph_nodes_from_response[0]), get_node_object_key(graph_nodes_from_response[1])]
    ordered_keys, key_to_node, visited = get_initial_graph_state(graph_nodes_from_response)
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
    node = {
        "id": 1,
        "otype": "table"
    }
    node_key = get_node_object_key(node)
    visited = {}
    key_to_node = {
        node_key: node,
    }
    descendant_nodes, visited = resolve_neighbors(node_key=node_key, visited=visited, key_to_node=key_to_node, allowed_types={"table"})
    assert descendant_nodes == []
    assert visited == {node_key: [node]}

def test_resolve_neighbors_unvisited_omitted_node_no_neighbors():
    node = {
        "id": 1,
        "otype": "dataflow"
    }
    node_key = get_node_object_key(node)
    visited = {}
    key_to_node = {
        node_key: node,
    }
    descendant_nodes, visited = resolve_neighbors(node_key=node_key, visited=visited, key_to_node=key_to_node, allowed_types={"view"})
    assert descendant_nodes == []
    assert visited == {node_key: []}

def test_resolve_neighbors_unvisited_allowed_node_with_neighbors():
    node2 = {
        "id": 2,
        "otype": "table"
    }
    node1 = {
        "id": 1,
        "otype": "table",
        "neighbors": [
            node2
        ]
    }
    node1_key = get_node_object_key(node1)
    node2_key = get_node_object_key(node2)

    visited = {}
    key_to_node = {
        node1_key: node1,
        node2_key: node2
    }
    descendant_nodes, visited = resolve_neighbors(node_key=node1_key, visited=visited, key_to_node=key_to_node, allowed_types={"table"})
    assert descendant_nodes == [node1]
    assert visited == {node1_key: [node1], node2_key: [node2]}

def test_resolve_neighbors_unvisited_omitted_node_with_neighbors():
    node2 = {
        "id": 2,
        "otype": "table"
    }
    node1 = {
        "id": 1,
        "otype": "dataflow",
        "neighbors": [
            node2
        ]
    }
    node1_key = get_node_object_key(node1)
    node2_key = get_node_object_key(node2)

    visited = {}
    key_to_node = {
        node1_key: node1,
        node2_key: node2
    }
    descendant_nodes, visited = resolve_neighbors(node_key=node1_key, visited=visited, key_to_node=key_to_node, allowed_types={"table"})
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
    descendant_nodes, visited = resolve_neighbors(node_key=node_key, visited=orig_visited, key_to_node=key_to_node, allowed_types={"table"})
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
    descendant_nodes, visited = resolve_neighbors(node_key=node_key, visited=orig_visited, key_to_node=key_to_node, allowed_types={"table"})
    assert descendant_nodes == []
    assert visited == orig_visited  # Should not change visited state

def test_filter_graph_basic():
    graph_nodes = [
        {
            "id": 1,
            "otype": "table",
            "neighbors": [
                {"id": 2, "otype": "table"},
                {"id": 3, "otype": "dataflow"}
            ]
        },
        {
            "id": 2,
            "otype": "table"
        },
        {
            "id": 3,
            "otype": "dataflow"
        }
    ]
    allowed_types = {"table"}
    filtered_graph = filter_graph(nodes=graph_nodes, allowed_types=allowed_types)
    assert len(filtered_graph) == 2  # Only table nodes should remain
    assert all(node["otype"] == "table" for node in filtered_graph)
    assert filtered_graph[0]["id"] == 1
    assert filtered_graph[1]["id"] == 2

def test_filter_graph_nested():
    graph_nodes = [
      {"id": 1, "otype": "table", "fully_qualified_name": "1", "neighbors": [{"id": 2, "otype": "table", "fully_qualified_name": "2"}]},
      {"id": 2, "otype": "table", "fully_qualified_name": "2", "neighbors": [{"id": 3, "otype": "etl", "fully_qualified_name": "3"}, {"id": 4, "otype": "table", "fully_qualified_name": "4"}]},
      {"id": 3, "otype": "etl", "fully_qualified_name": "3", "neighbors": [{"id": 5, "otype": "table", "fully_qualified_name": "5"}]},
      {"id": 4, "otype": "table", "fully_qualified_name": "4", "neighbors": []},
      {"id": 5, "otype": "table", "fully_qualified_name": "5", "neighbors": []},
      {"id": 6, "otype": "table", "fully_qualified_name": "6", "neighbors": [{"id": 3, "otype": "etl", "fully_qualified_name": "3"}]},
      {"id": 7, "otype": "etl", "fully_qualified_name": "7", "neighbors": [{"id": 8, "otype": "etl", "fully_qualified_name": "8"}]},
      {"id": 8, "otype": "etl", "fully_qualified_name": "8", "neighbors": []},
      {"id": 9, "otype": "etl", "fully_qualified_name": "9", "neighbors": [{"id": 10, "otype": "table", "fully_qualified_name": "10"}]},
      {"id": 10, "otype": "table", "fully_qualified_name": "10", "neighbors": []}
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
        "table:1": {"id": 1, "otype": "table", "neighbors": [{"id": 2, "otype": "table", "neighbors": [{"id": 4, "otype": "throw_away"}]}]},
        "table:2": {"id": 2, "otype": "table"},
        "dataflow:3": {"id": 3, "otype": "dataflow"}
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
    return Mock()

@pytest.fixture
def get_lineage_tool(mock_api):
    """Creates an AlationLineageTool with mock API."""
    return AlationLineageTool(mock_api)

def test_alation_lineage_tool_should_invoke_make_lineage_kwargs(get_lineage_tool):
    with patch("alation_ai_agent_sdk.tools.make_lineage_kwargs") as mock_make_lineage_kwargs:
        get_lineage_tool.run(
            root_node={
                "id": 1,
                "otype": "table",
            },
            direction="downstream"
        )
        mock_make_lineage_kwargs.assert_called_once()


def test_alation_lineage_tool_returns_api_errors(get_lineage_tool, mock_api):
    # Mock API error
    api_error = AlationAPIError(
        message="Bad Request",
        status_code=400,
        reason="Bad Request",
        resolution_hint="Check API parameters"
    )
    mock_api.get_bulk_lineage.side_effect = api_error
    result = get_lineage_tool.run(
        root_node={"id": 1, "otype": "table"},
        direction="downstream",
        limit=100,
        batch_size=100,
    )
    mock_api.get_bulk_lineage.assert_called_once()
    # Verify error handling
    assert "error" in result
    assert result["error"]["message"] == "Bad Request"
    assert result["error"]["status_code"] == 400
    assert result["error"]["reason"] == "Bad Request"


def test_alation_lineage_tool_raises_value_errors_during_validation(
    mock_requests_post,
    mock_requests_get,
):
    mock_requests_post("createAPIAccessToken", response_json=REFRESH_TOKEN_RESPONSE_SUCCESS)
    mock_requests_post("oauth/v2/token", response_json=JWT_RESPONSE_SUCCESS)
    mock_requests_get("license", response_json={"is_cloud": True})
    mock_requests_get("full_version", response_json={"ALATION_RELEASE_NAME": "2025.1.2"})

    api = AlationAPI(
        base_url="https://api.alation.com",
        auth_method="user_account",
        auth_params=UserAccountAuthParams(
            111,
            refresh_token="mock-refresh-token"
        )
    )
    with pytest.raises(ValueError) as ex:
        api.get_bulk_lineage(
            root_nodes=[{"id": 1, "otype": "table"}],
            direction="downstream",
            limit=10000,
            batch_size=10000,
            processing_mode=LineageGraphProcessingOptions.COMPLETE,
            allowed_otypes=None,
            excluded_schema_ids=None,
            max_depth=1000,
            show_temporal_objects=False,
            key_type="id",
            design_time=LineageDesignTimeOptions.EITHER_DESIGN_OR_RUN_TIME,
            time_from="",
            time_to="",
            pagination=None,
        )
    assert "limit cannot exceed" in str(ex.value)
    with pytest.raises(ValueError) as ex:
        api.get_bulk_lineage(
            root_nodes=[{"id": 1, "otype": "table"}],
            limit=1000,
            batch_size=1000,
            direction="downstream",
            allowed_otypes=[],
            processing_mode=LineageGraphProcessingOptions.COMPLETE,
            excluded_schema_ids=None,
            max_depth=1000,
            show_temporal_objects=False,
            key_type="id",
            design_time=LineageDesignTimeOptions.EITHER_DESIGN_OR_RUN_TIME,
            time_from="",
            time_to="",
            pagination=None,
        )
    assert "cannot be empty list" in str(ex.value)
    with pytest.raises(ValueError) as ex:
        api.get_bulk_lineage(
            root_nodes=[{"id": 1, "otype": "table"}],
            direction="downstream",
            limit=1000,
            batch_size=1000,
            allowed_otypes=["table"],
            processing_mode=LineageGraphProcessingOptions.CHUNKED,
            excluded_schema_ids=None,
            max_depth=1000,
            show_temporal_objects=False,
            key_type="id",
            design_time=LineageDesignTimeOptions.EITHER_DESIGN_OR_RUN_TIME,
            time_from="",
            time_to="",
            pagination=None,
        )
    assert "only supported in 'complete' processing mode" in str(ex.value)
    with pytest.raises(ValueError) as ex:
        api.get_bulk_lineage(
            root_nodes=[{"id": 1, "otype": "table"}],
            direction="downstream",
            limit=1000,
            batch_size=1000,
            allowed_otypes=["table"],
            processing_mode=LineageGraphProcessingOptions.COMPLETE,
            pagination={
                "request_id": "123",
                "batch_size": 1000,
                "cursor": 123,
                "has_more": True
            },
            excluded_schema_ids=None,
            max_depth=1000,
            show_temporal_objects=False,
            key_type="id",
            design_time=LineageDesignTimeOptions.EITHER_DESIGN_OR_RUN_TIME,
            time_from="",
            time_to="",
        )
    assert "only supported in 'chunked' processing mode" in str(ex.value)

@pytest.fixture
def alation_api(mock_requests_get, mock_requests_post):
    mock_requests_post("createAPIAccessToken", response_json=REFRESH_TOKEN_RESPONSE_SUCCESS)
    mock_requests_post("oauth/v2/token", response_json=JWT_RESPONSE_SUCCESS)
    mock_requests_get("license", response_json={"is_cloud": True})
    mock_requests_get("full_version", response_json={"ALATION_RELEASE_NAME": "2025.1.2"})

    """Fixture to initialize AlationAPI instance."""
    api = AlationAPI(
        base_url="https://api.alation.com",
        auth_method="user_account",
        auth_params=UserAccountAuthParams(
            111,
            refresh_token="mock-refresh-token"
        )
    )
    return api


def test_get_bulk_lineage_success_complete_filtered_with_pagination_response(alation_api, mock_requests_post, mock_requests_get):
    mock_requests_post("createAPIAccessToken", response_json=REFRESH_TOKEN_RESPONSE_SUCCESS)
    mock_requests_post("oauth/v2/token", response_json=JWT_RESPONSE_SUCCESS)
    mock_requests_get("license", response_json={"is_cloud": True})
    mock_requests_get("full_version", response_json={"ALATION_RELEASE_NAME": "2025.1.2"})
    graph_nodes = [
      {"id": 1, "otype": "table", "fully_qualified_name": "1", "neighbors": [{"id": 2, "otype": "table", "fully_qualified_name": "2"}]},
      {"id": 2, "otype": "table", "fully_qualified_name": "2", "neighbors": [{"id": 3, "otype": "etl", "fully_qualified_name": "3"}, {"id": 4, "otype": "table", "fully_qualified_name": "4"}]},
      {"id": 3, "otype": "etl", "fully_qualified_name": "3", "neighbors": [{"id": 5, "otype": "table", "fully_qualified_name": "5"}]},
      {"id": 4, "otype": "table", "fully_qualified_name": "4", "neighbors": []},
      {"id": 5, "otype": "table", "fully_qualified_name": "5", "neighbors": []},
      {"id": 6, "otype": "table", "fully_qualified_name": "6", "neighbors": [{"id": 3, "otype": "etl", "fully_qualified_name": "3"}]},
      {"id": 7, "otype": "etl", "fully_qualified_name": "7", "neighbors": [{"id": 8, "otype": "etl", "fully_qualified_name": "8"}]},
      {"id": 8, "otype": "etl", "fully_qualified_name": "8", "neighbors": []},
      {"id": 9, "otype": "etl", "fully_qualified_name": "9", "neighbors": [{"id": 10, "otype": "table", "fully_qualified_name": "10"}]},
      {"id": 10, "otype": "table", "fully_qualified_name": "10", "neighbors": []}
    ]
    mock_requests_post(
        alation_api.base_url + "/integration/v2/bulk_lineage/",
        response_json=
            {
                "graph": graph_nodes,
                "direction": "upstream",
                "request_id": "123",
                "Pagination": {
                    "cursor": 123,
                    "has_more": True,
                    "batch_size": 1000,
                }
            },
        status_code=200,
    )
    result = alation_api.get_bulk_lineage(
        root_nodes=[{"id": 1, "otype": "table"}],
        direction="upstream",
        limit=1000,
        batch_size=1000,
        processing_mode=LineageGraphProcessingOptions.COMPLETE,
        show_temporal_objects=False,
        design_time=LineageDesignTimeOptions.EITHER_DESIGN_OR_RUN_TIME,
        max_depth=10,
        excluded_schema_ids=None,
        allowed_otypes=["table"],
        time_from="",
        time_to="",
        key_type="id",
        pagination=None,
    )
    assert "graph" in result
    assert "direction" in result
    assert result["direction"] == "upstream"


    assert "pagination" in result
    assert result["pagination"] == {
            "cursor": 123,
            "request_id": "123",
            "has_more": True,
            "batch_size": 1000,
        }
    filtered_graph = result["graph"]
    assert len(filtered_graph) == 6  # Only table nodes should remain
    assert all(node["otype"] == "table" for node in filtered_graph)
    assert filtered_graph[0]["id"] == graph_nodes[0]["id"]
    assert filtered_graph[1]["id"] == graph_nodes[1]["id"]
    assert filtered_graph[2]["id"] == graph_nodes[3]["id"]
    assert filtered_graph[3]["id"] == graph_nodes[4]["id"]
    assert filtered_graph[4]["id"] == graph_nodes[5]["id"]
    assert filtered_graph[5]["id"] == graph_nodes[9]["id"]

def test_get_bulk_lineage_success_chunked(alation_api, mock_requests_post, mock_requests_get):
    mock_requests_post("createAPIAccessToken", response_json=REFRESH_TOKEN_RESPONSE_SUCCESS)
    mock_requests_post("oauth/v2/token", response_json=JWT_RESPONSE_SUCCESS)
    mock_requests_get("license", response_json={"is_cloud": True})
    mock_requests_get("full_version", response_json={"ALATION_RELEASE_NAME": "2025.1.2"})

    graph_nodes = [
      {"id": 1, "otype": "table", "fully_qualified_name": "1", "neighbors": [{"id": 2, "otype": "table", "fully_qualified_name": "2"}]},
      {"id": 2, "otype": "table", "fully_qualified_name": "2", "neighbors": [{"id": 3, "otype": "etl", "fully_qualified_name": "3"}, {"id": 4, "otype": "table", "fully_qualified_name": "4"}]},
      {"id": 3, "otype": "etl", "fully_qualified_name": "3", "neighbors": [{"id": 5, "otype": "table", "fully_qualified_name": "5"}]},
      {"id": 4, "otype": "table", "fully_qualified_name": "4", "neighbors": []},
      {"id": 5, "otype": "table", "fully_qualified_name": "5", "neighbors": []},
      {"id": 6, "otype": "table", "fully_qualified_name": "6", "neighbors": [{"id": 3, "otype": "etl", "fully_qualified_name": "3"}]},
      {"id": 7, "otype": "etl", "fully_qualified_name": "7", "neighbors": [{"id": 8, "otype": "etl", "fully_qualified_name": "8"}]},
      {"id": 8, "otype": "etl", "fully_qualified_name": "8", "neighbors": []},
      {"id": 9, "otype": "etl", "fully_qualified_name": "9", "neighbors": [{"id": 10, "otype": "table", "fully_qualified_name": "10"}]},
      {"id": 10, "otype": "table", "fully_qualified_name": "10", "neighbors": []}
    ]
    mock_requests_post(
        alation_api.base_url + "/integration/v2/bulk_lineage/",
        response_json=
            {
                "graph": graph_nodes,
                "direction": "upstream",
                "request_id": "123",
            },
        status_code=200,
    )
    result = alation_api.get_bulk_lineage(
        root_nodes=[{"id": 1, "otype": "table"}],
        direction="upstream",
        limit=1000,
        batch_size=1000,
        processing_mode=LineageGraphProcessingOptions.CHUNKED,
        show_temporal_objects=False,
        design_time=LineageDesignTimeOptions.EITHER_DESIGN_OR_RUN_TIME,
        max_depth=10,
        excluded_schema_ids=None,
        allowed_otypes=None,
        time_from="",
        time_to="",
        key_type="id",
        pagination={
            "cursor": 123,
            "request_id": "123",
            "has_more": True,
            "batch_size": 1000,
        },
    )
    assert "graph" in result
    assert "direction" in result
    assert result["direction"] == "upstream"

    chunked_graph = result["graph"]

    assert "pagination" not in result
    assert len(chunked_graph) == len(graph_nodes)
    assert chunked_graph[0]["id"] == graph_nodes[0]["id"]
    assert chunked_graph[1]["id"] == graph_nodes[1]["id"]
    assert chunked_graph[2]["id"] == graph_nodes[2]["id"]
    assert chunked_graph[3]["id"] == graph_nodes[3]["id"]
    assert chunked_graph[4]["id"] == graph_nodes[4]["id"]
    assert chunked_graph[5]["id"] == graph_nodes[5]["id"]
    assert chunked_graph[6]["id"] == graph_nodes[6]["id"]
    assert chunked_graph[7]["id"] == graph_nodes[7]["id"]
    assert chunked_graph[8]["id"] == graph_nodes[8]["id"]
    assert chunked_graph[9]["id"] == graph_nodes[9]["id"]
