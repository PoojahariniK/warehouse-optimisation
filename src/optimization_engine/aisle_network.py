"""
Aisle Network Module — CAP-12 Warehouse Slotting & Pick-Path Optimization.

Builds a weighted undirected graph of warehouse locations and applies
Dijkstra's algorithm to find aisle-constrained shortest walking paths.

NOTE: This module uses a *simulated* warehouse connectivity model based on
      the coordinate layout in warehouse_locations_clean.csv. It does NOT
      represent a verified physical warehouse floor plan. Assumptions:
        - Same-aisle locations are connected to consecutive Y-neighbors.
        - Adjacent aisles (by X coordinate) are connected at matching Y values.
        - All connections are bidirectional.
        - Diagonal movement is NOT allowed.
        - No blocked or one-way paths in this prototype.
"""

import heapq
import logging
import math
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

# Graph type alias: adjacency list  {node_id: [(neighbor_id, weight), ...]}
Graph = Dict[str, List[Tuple[str, float]]]


# ---------------------------------------------------------------------------
# 1. Build Warehouse Graph
# ---------------------------------------------------------------------------

def build_warehouse_graph(locations_df: pd.DataFrame) -> Graph:
    """
    Constructs a weighted undirected adjacency-list graph from the warehouse
    locations DataFrame.

    Connectivity rules (simulated — see module docstring):
      - Same aisle: connect consecutive locations sorted by Y ascending.
      - Cross aisle: for each Y value, connect adjacent aisle locations
        sorted by X ascending.
      - Edge weight = Euclidean distance between coordinates (reduces to
        |ΔY| for same-aisle edges and |ΔX| for cross-aisle edges because
        no diagonal movement is allowed).

    Args:
        locations_df: DataFrame with columns
            Location_ID, Aisle, X, Y (at minimum).

    Returns:
        Graph (dict): adjacency list keyed by Location_ID.
    """
    df = locations_df.copy()

    # Validate required columns
    required_cols = {"Location_ID", "Aisle", "X", "Y"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"warehouse_locations DataFrame is missing columns: {missing}")

    # Coerce X, Y to float
    try:
        df["X"] = df["X"].astype(float)
        df["Y"] = df["Y"].astype(float)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Non-numeric X or Y values found in locations data: {exc}") from exc

    # Validate no duplicate Location_IDs
    dup_ids = df[df.duplicated("Location_ID")]["Location_ID"].tolist()
    if dup_ids:
        raise ValueError(f"Duplicate Location_IDs found: {dup_ids}")

    # Initialise empty adjacency list for every location
    graph: Graph = {loc_id: [] for loc_id in df["Location_ID"]}

    coord_map: Dict[str, Tuple[float, float]] = {
        row["Location_ID"]: (row["X"], row["Y"])
        for _, row in df.iterrows()
    }

    added_edges: Set[Tuple[str, str]] = set()

    def _add_edge(a: str, b: str) -> None:
        """Add a bidirectional edge if not already present."""
        key = tuple(sorted([a, b]))
        if key in added_edges:
            return
        if a not in graph or b not in graph:
            logger.warning("Edge references unknown location(s): %s — %s. Skipping.", a, b)
            return
        ax, ay = coord_map[a]
        bx, by = coord_map[b]
        weight = round(math.sqrt((bx - ax) ** 2 + (by - ay) ** 2), 6)
        graph[a].append((b, weight))
        graph[b].append((a, weight))
        added_edges.add(key)

    # ---- Same-aisle edges (consecutive locations by Y) ----
    for aisle_name, aisle_df in df.groupby("Aisle"):
        sorted_aisle = aisle_df.sort_values("Y").reset_index(drop=True)
        for i in range(len(sorted_aisle) - 1):
            loc_a = sorted_aisle.loc[i, "Location_ID"]
            loc_b = sorted_aisle.loc[i + 1, "Location_ID"]
            _add_edge(loc_a, loc_b)

    # ---- Cross-aisle edges (adjacent aisles at same Y) ----
    # Group by Y; within each Y row, sort by X and connect consecutive X-neighbors.
    for y_val, y_group in df.groupby("Y"):
        sorted_y = y_group.sort_values("X").reset_index(drop=True)
        for i in range(len(sorted_y) - 1):
            loc_a = sorted_y.loc[i, "Location_ID"]
            loc_b = sorted_y.loc[i + 1, "Location_ID"]
            _add_edge(loc_a, loc_b)

    logger.info(
        "Warehouse graph built: %d nodes, %d unique edges (simulated aisle connectivity).",
        len(graph),
        len(added_edges),
    )
    return graph


# ---------------------------------------------------------------------------
# 2. Dispatch Point Support
# ---------------------------------------------------------------------------

def get_dispatch_node(
    graph: Graph,
    dispatch_point: Tuple[float, float],
    locations_df: pd.DataFrame,
) -> str:
    """
    Returns the graph node that represents the dispatch / depot point.

    Strategy:
      1. If a warehouse location already has coordinates equal to
         dispatch_point, use that Location_ID directly (no virtual node).
      2. Otherwise, create a virtual "DISPATCH" node and connect it to the
         nearest warehouse location by straight-line distance.

    Args:
        graph:          Adjacency-list graph (mutated in-place only if a
                        virtual node is required).
        dispatch_point: (X, Y) coordinates of the dispatch station.
        locations_df:   Warehouse locations DataFrame.

    Returns:
        Node identifier (string) to use as the start/end of every route.
    """
    dx, dy = float(dispatch_point[0]), float(dispatch_point[1])

    df = locations_df.copy()
    df["X"] = df["X"].astype(float)
    df["Y"] = df["Y"].astype(float)

    # Check if any existing location coincides with dispatch coords
    match = df[(df["X"] == dx) & (df["Y"] == dy)]
    if not match.empty:
        matched_id = match.iloc[0]["Location_ID"]
        logger.info(
            "Dispatch point (%.1f, %.1f) coincides with existing location '%s'. "
            "Using '%s' as dispatch node — no virtual node created.",
            dx, dy, matched_id, matched_id,
        )
        return matched_id

    # No exact match — create virtual "DISPATCH" node
    logger.info(
        "Dispatch point (%.1f, %.1f) does not coincide with any warehouse location. "
        "Creating virtual 'DISPATCH' node.",
        dx, dy,
    )
    if "DISPATCH" not in graph:
        graph["DISPATCH"] = []

    # Connect DISPATCH to the nearest existing location
    nearest_id: Optional[str] = None
    nearest_dist = float("inf")
    for _, row in df.iterrows():
        d = math.sqrt((row["X"] - dx) ** 2 + (row["Y"] - dy) ** 2)
        if d < nearest_dist:
            nearest_dist = d
            nearest_id = row["Location_ID"]

    if nearest_id is not None:
        weight = round(nearest_dist, 6)
        graph["DISPATCH"].append((nearest_id, weight))
        graph[nearest_id].append(("DISPATCH", weight))
        logger.info(
            "Virtual DISPATCH node connected to '%s' (distance = %.2f).",
            nearest_id, weight,
        )

    return "DISPATCH"


# ---------------------------------------------------------------------------
# 3. Dijkstra's Shortest-Path Algorithm
# ---------------------------------------------------------------------------

def find_shortest_path(
    graph: Graph,
    start_node: str,
    end_node: str,
) -> Tuple[float, List[str]]:
    """
    Finds the shortest path between two nodes using Dijkstra's algorithm.

    Uses a min-heap (heapq) for O((V + E) log V) efficiency.

    Args:
        graph:      Weighted adjacency-list graph.
        start_node: Starting node identifier.
        end_node:   Destination node identifier.

    Returns:
        (distance, path) where:
          - distance is the total walking distance (float); returns inf if
            the destination is unreachable.
          - path is an ordered list of node IDs from start to end (inclusive);
            returns an empty list if unreachable.
    """
    if start_node not in graph:
        logger.warning("Start node '%s' not found in graph.", start_node)
        return float("inf"), []
    if end_node not in graph:
        logger.warning("End node '%s' not found in graph.", end_node)
        return float("inf"), []
    if start_node == end_node:
        return 0.0, [start_node]

    # Priority queue entries: (cumulative_distance, current_node)
    heap: List[Tuple[float, str]] = [(0.0, start_node)]
    dist: Dict[str, float] = {start_node: 0.0}
    prev: Dict[str, Optional[str]] = {start_node: None}

    while heap:
        current_dist, current_node = heapq.heappop(heap)

        # Early exit
        if current_node == end_node:
            break

        # Skip stale entries
        if current_dist > dist.get(current_node, float("inf")):
            continue

        for neighbor, weight in graph.get(current_node, []):
            new_dist = current_dist + weight
            if new_dist < dist.get(neighbor, float("inf")):
                dist[neighbor] = new_dist
                prev[neighbor] = current_node
                heapq.heappush(heap, (new_dist, neighbor))

    total_dist = dist.get(end_node, float("inf"))

    if total_dist == float("inf"):
        logger.warning(
            "No path found from '%s' to '%s'. "
            "Check warehouse connectivity or graph construction.",
            start_node, end_node,
        )
        return float("inf"), []

    # Reconstruct path
    path: List[str] = []
    node: Optional[str] = end_node
    while node is not None:
        path.append(node)
        node = prev.get(node)
    path.reverse()

    return round(total_dist, 6), path


def get_shortest_distance(
    graph: Graph,
    start_node: str,
    end_node: str,
) -> float:
    """
    Convenience wrapper — returns only the shortest walking distance.

    Returns float('inf') if the destination is unreachable.
    """
    distance, _ = find_shortest_path(graph, start_node, end_node)
    return distance


# ---------------------------------------------------------------------------
# 4. Graph Validation
# ---------------------------------------------------------------------------

def validate_graph(graph: Graph, locations_df: pd.DataFrame) -> None:
    """
    Runs sanity checks on the constructed graph and logs warnings.

    Checks:
      - Every Location_ID in the DataFrame has a node in the graph.
      - No unexpected extra nodes (beyond warehouse locations + DISPATCH).
      - No node is isolated (zero neighbours).
      - Warns if any node is unreachable from A01 (or the first node).

    Args:
        graph:        Graph to validate.
        locations_df: Warehouse locations DataFrame.

    Raises:
        ValueError: If any Location_ID is missing from the graph.
    """
    location_ids = set(locations_df["Location_ID"].tolist())
    graph_nodes = set(graph.keys()) - {"DISPATCH"}

    missing_in_graph = location_ids - graph_nodes
    if missing_in_graph:
        raise ValueError(
            f"These warehouse locations have no graph node: {sorted(missing_in_graph)}"
        )

    extra_nodes = graph_nodes - location_ids
    if extra_nodes:
        logger.warning("Graph contains unexpected extra nodes: %s", extra_nodes)

    # Isolated nodes
    isolated = [n for n, neighbors in graph.items() if len(neighbors) == 0]
    if isolated:
        logger.warning("Isolated nodes (no connections) detected: %s", isolated)

    # Reachability from first warehouse node
    start = next(iter(location_ids))
    reachable: Set[str] = set()
    stack = [start]
    while stack:
        node = stack.pop()
        if node in reachable:
            continue
        reachable.add(node)
        for neighbor, _ in graph.get(node, []):
            if neighbor not in reachable:
                stack.append(neighbor)

    unreachable = location_ids - reachable
    if unreachable:
        logger.warning(
            "The following warehouse locations are unreachable from '%s': %s",
            start, sorted(unreachable),
        )
    else:
        logger.info("Graph validation passed: all %d warehouse locations are connected.", len(location_ids))

