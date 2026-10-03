from dataclasses import dataclass, field
from enum import Enum


class ZoneType(Enum):
    normal = "normal"
    blocked = "blocked"
    restricted = "restricted"
    priority = "priority"


@dataclass
class ZoneMetadata:
    zone_type: ZoneType
    color: str | None = None
    max_drones: int = 1


@dataclass
class Zone:
    name: str
    x: int
    y: int
    metadata: ZoneMetadata
    current_drones: list["Drone"] = field(default_factory=list)

    def entry_cost(self) -> int|float:
        """Return the number of turns required to enter this zone."""
        ztype = self.metadata.zone_type
        if ztype == "priority":
            return float(0.8)
        if ztype == "restricted":
            return 2
        if ztype == "blocked":
            raise ValueError("blocked zone has no entry cost")
            return float('inf')
            #or we can add in the pahfinding to ignore blocked zones 
        return 1


@dataclass
class Connection:
    zone_a: Zone
    zone_b: Zone
    max_link_capacity: int = 1
    in_transit: list["Drone"] = field(default_factory=list)


@dataclass
class Drone:
    id: int
    current_zone: str | None
    target_zone: str | None = None
    turns_remaining: int = 0


@dataclass
class Network:
    nb_drones: int
    start:     Zone
    end:       Zone
    zones:     dict[str, Zone]
    connections: list[Connection]

    def get_zone(self, name) -> Zone:
        return self.zones[name]

    def neighbors(self, zone_name) -> list[Zone]:
        neighbor = []
        for n in self.connections:
            if n.zone_a.name == zone_name:
                neighbor.append(n.zone_b)
            if n.zone_b.name == zone_name:
                neighbor.append(n.zone_a)
        return neighbor

    def connection_between(self, a, b) -> Connection | None:
        for conn in self.connections:
            if a == conn.zone_a and b == conn.zone_b:
                return conn
            if a == conn.zone_b and b == conn.zone_a:
                return conn
            continue
        return None
