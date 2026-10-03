"""Shortest-path computation over the drone network.

Uses Dijkstra on a graph whose node weights are the entry costs of zones
(see Zone.entry_cost). Blocked zones are excluded from the graph.

Costs are non-negative integers, so Dijkstra is correct.
"""

from src import models


def shortest_path(
    network: models.Network,
    start: models.Zone,
    end: models.Zone,
) -> list[models.Zone] | None:
    """Return the cheapest path from start to end, or None if unreachable.

    The returned list includes both start and end.
    """
    ...