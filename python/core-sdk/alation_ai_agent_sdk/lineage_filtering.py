from typing import List, Dict, Set, Union
from typing_extensions import TypedDict

OType = str
class LineageGraphNode(TypedDict):
    fully_qualified_name: str
    id: Union[str, int]
    otype: OType
    neighbors: List['LineageGraphNode']


def get_node_object_key(node: LineageGraphNode) -> str:
    """
    Returns a unique key for the node based on its type and ID.

    Args:
        node (LineageGraphNode): The node to generate the key for.

    Returns:
        str: A unique key for the node.
    """
    return f"{node['otype']}:{node['id']}"


def get_initial_graph_state(
    nodes: List[Dict],
  ) -> tuple[List[str], Dict[str, Dict], Set[str]]:
    """
    Get the initial state of the graph from the list of nodes.

    Args:
        nodes (List[Dict]): The list of nodes to process.

    Returns:
        tuple[List[str], Dict[str, Dict], Set[str]]: A tuple containing:
            - A list of ordered node keys.
            - A mapping from node keys to their original node data.
            - A set of visited node keys.
    """
    ordered_keys = []
    key_to_node = {}
    for node in nodes:
        node_key = get_node_object_key(node)
        key_to_node[node_key] = node
        ordered_keys.append(node_key)
    visited = {}
    return (ordered_keys, key_to_node, visited)


# Returns list of descendant nodes that are allowed (flattened and reattached)
def resolve_neighbors(
    node_key: str,
    key_to_node: Dict[str, Dict],
    visited: Dict[str, List[Dict]],
    allowed_types: Set[str],
) -> tuple[List[Dict], Dict[str, List[Dict]]]:
    """
    Resolves the neighbors of a given node, returning the allowed descendant nodes.

    Args:
        node_key (str): The key of the node to resolve neighbors for.
        key_to_node (Dict[str, Dict]): A mapping from node keys to their original node data.
        visited (Dict[str, List[Dict]]): A mapping of visited nodes and their descendants.
        allowed_types (Set[str]): A set of allowed node types.

    Returns:
        tuple[List[Dict], Dict[str, List[Dict]]]: A tuple containing:
            - A list of allowed descendant nodes.
            - An updated mapping of visited nodes and their descendants.
    """
    if node_key in visited:
        return (visited[node_key], visited)

    node = key_to_node[node_key]
    if node['otype'] in allowed_types:
        new_neighbors = []
        if "neighbors" not in node:
            visited[node_key] = [key_to_node[node_key]]
            return (new_neighbors, visited)

        for neighbor_node in node["neighbors"]:
            neighbor_key = get_node_object_key(neighbor_node)
            neighbors_neighbors, visited = resolve_neighbors(neighbor_key, key_to_node, visited, allowed_types)
            new_neighbors.extend(neighbors_neighbors)
        visited[node_key] = [key_to_node[node_key]]
        unique_new_neighbors = {get_node_object_key(n): n for n in new_neighbors}
        node['neighbors'] = [
            new_neighbor
            for new_neighbor in new_neighbors
            if get_node_object_key(new_neighbor) in unique_new_neighbors
          ]
        return ([key_to_node[node_key]], visited)

    # Omit this node, but keep its children (recursively)
    collected = []
    if "neighbors" not in node:
        visited[node_key] = collected
        return (collected, visited)
    for neighbor_node in node["neighbors"]:
        neighbor_key = get_node_object_key(neighbor_node)
        neighbors_neighbors, visited = resolve_neighbors(neighbor_key, key_to_node, visited, allowed_types)
        collected.extend(neighbors_neighbors)
    visited[node_key] = collected
    return (collected, visited)


def filter_graph(nodes: List[Dict], allowed_types: Set[str]) -> List[Dict]:
    """
    Filters the graph to only include nodes of allowed types and their descendants.
    Maintains hierarchical relationships between nodes even when omitting some.

    Args:
        nodes (List[Dict]): The list of nodes to filter.
        allowed_types (Set[str]): A set of allowed node types.

    Returns:
        List[Dict]: The filtered list of nodes.
    """
    ordered_keys, key_to_node, visited = get_initial_graph_state(nodes)

    # Populate the visited nodes and patch up neighbors to account for any that were omitted
    for node in nodes:
        resolve_neighbors(get_node_object_key(node), key_to_node, visited, allowed_types)
    kept_keys = {node_key for node_key in visited if key_to_node[node_key]['otype'] in allowed_types}
    # Free the memory before we build the filtered graph
    visited = {}

    new_nodes = build_filtered_graph(ordered_keys, kept_keys, key_to_node)
    return new_nodes


def build_filtered_graph(
      ordered_keys: List[str],
      kept_keys: Set[str],
      key_to_node: Dict[str, Dict],
) -> List[Dict]:
    """
    Builds the filtered graph from the ordered keys and kept keys.

    Args:
        ordered_keys (List[str]): The list of ordered node keys.
        kept_keys (Set[str]): A set of kept node keys.
        key_to_node (Dict[str, Dict]): A mapping from node keys to their original node data.

    Returns:
        List[Dict]: The filtered list of nodes which represent the lineage graph.
    """
    new_nodes = []
    for node_key in ordered_keys:
        if node_key not in kept_keys:
            continue
        original_node = key_to_node[node_key]
        new_node = {
            "id": original_node["id"],
            "otype": original_node["otype"],
        }
        if "fully_qualified_name" in original_node:
            new_node["fully_qualified_name"] = original_node["fully_qualified_name"]
        new_node["neighbors"] = [
            n for n in original_node.get("neighbors", []) if get_node_object_key(n) in kept_keys
        ]
        new_nodes.append(new_node)
    # Each item in the list have have neighbors but their neighbors are not allowed otherwise we're repeating
    # it in the nested structure at at the item list level.
    for node in new_nodes:
        if len(node["neighbors"]) == 0:
            continue
        for neighbor_node in node["neighbors"]:
            if "neighbors" in neighbor_node:
                del neighbor_node["neighbors"]

    return new_nodes