"""
Greedy approximate TSP solver for visit order using a distance matrix.

This is **not** an exact TSP solver — it uses a nearest-neighbor heuristic,
which is easy to read and works well for small sightseeing lists (typical
itineraries). Pairwise distances should come from ``maps_service.distance_matrix``.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Sequence, Tuple

logger = logging.getLogger(__name__)


def _extract_matrix(
    matrix_payload: Dict[str, Any],
) -> Tuple[List[List[float]], List[List[float]]]:
    """
    Build square matrices for distance (meters) and duration (seconds).

    Missing or non-OK cells use ``math.inf`` for distance and ``0`` for duration.
    """
    rows = matrix_payload.get("rows") or []
    size = len(rows)
    if size == 0:
        return [], []

    dist: List[List[float]] = [[math.inf] * size for _ in range(size)]
    dur: List[List[float]] = [[0.0] * size for _ in range(size)]
    for r_idx, row in enumerate(rows):
        for element in row.get("elements") or []:
            c_idx = int(element.get("destination_index", 0))
            if element.get("status") == "OK":
                dist[r_idx][c_idx] = float(element.get("distance_meters", math.inf))
                dur[r_idx][c_idx] = float(element.get("duration_seconds", 0) or 0)
            else:
                dist[r_idx][c_idx] = math.inf
                dur[r_idx][c_idx] = 0.0

    return dist, dur


def optimize_visit_order(
    attractions: Sequence[Dict[str, Any]],
    distance_matrix_payload: Dict[str, Any],
    *,
    start_index: int = 0,
) -> Dict[str, Any]:
    """
    Compute an order that approximately minimizes total travel distance.

    Algorithm (nearest neighbor):
    1. Start at ``start_index``.
    2. Repeatedly visit the closest not-yet-visited location (by road distance).
    3. Sum distances along the chosen edges where available.

    Args:
        attractions: list of dicts with at least ``name``, ``latitude``, ``longitude``.
        distance_matrix_payload: output from ``maps_service.distance_matrix`` / ``fetch_route_data_for_attractions``.
        start_index: which attraction to treat as the first stop (default first list item).

    Returns:
        JSON-serializable summary including ordered names and totals.
    """
    places = list(attractions)
    if not places:
        return {
            "ordered_indices": [],
            "ordered_names": [],
            "total_distance_meters": 0,
            "total_duration_seconds": None,
            "algorithm": "nearest_neighbor_tsp",
            "note": "No attractions provided.",
        }

    dist, dur = _extract_matrix(distance_matrix_payload)
    n = len(places)
    if len(dist) != n:
        logger.warning("Distance matrix size mismatch; returning input order.")
        return {
            "ordered_indices": list(range(n)),
            "ordered_names": [p.get("name") or f"Place {i}" for i, p in enumerate(places)],
            "total_distance_meters": None,
            "total_duration_seconds": None,
            "algorithm": "input_order_fallback",
            "note": "Matrix size did not match attractions; kept original order.",
        }

    unvisited = set(range(n))
    if start_index not in unvisited:
        start_index = 0

    order: List[int] = []
    current = start_index
    unvisited.remove(current)
    order.append(current)
    total_distance = 0.0
    total_duration = 0.0

    while unvisited:
        nearest = min(unvisited, key=lambda idx: dist[current][idx])
        leg_dist = dist[current][nearest]
        leg_dur = dur[current][nearest]
        if math.isfinite(leg_dist):
            total_distance += leg_dist
            total_duration += leg_dur
        else:
            logger.warning("Non-finite distance between %s and %s — stopping early.", current, nearest)
            break
        current = nearest
        unvisited.remove(current)
        order.append(current)

    # append any leftovers in stable order (disconnected graph edge case)
    for idx in sorted(unvisited):
        order.append(idx)

    ordered_names = [places[i].get("name") or f"Place {i}" for i in order]

    result = {
        "ordered_indices": order,
        "ordered_names": ordered_names,
        "total_distance_meters": int(total_distance) if math.isfinite(total_distance) else None,
        "total_duration_seconds": int(total_duration) if total_duration > 0 else None,
        "algorithm": "nearest_neighbor_tsp",
        "note": "Optimized using road distances; durations summed from the same Distance Matrix response.",
    }
    logger.info("Route optimized | stops=%s | approx_distance_m=%s", len(order), result["total_distance_meters"])
    return result
