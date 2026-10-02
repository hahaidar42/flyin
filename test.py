import re
from src import models


class ParsingError(Exception):
    def __init__(
        self,
        message: str,
        line_number: int | None = None,
        line_content: str | None = None,
    ) -> None:
        self.message = message
        self.line_number = line_number
        self.line_content = line_content

        parts = []
        if line_number is not None:
            parts.append(f"Line {line_number}")
        if line_content is not None:
            parts.append(f"`{line_content.strip()}`")
        if parts:
            full_msg = f"{' | '.join(parts)}: {message}"
        else:
            full_msg = message

        super().__init__(full_msg)


def parse_file(filename):
    zones: dict[str, models.Zone] = {}
    start:          models.Zone | None = None
    end:            models.Zone | None = None
    nb_drones:      int | None = None
    raw_conns:      list[tuple[str, str, str | None, int, str]] = []
    conns:      list[models.Connection] = []
    line_num: int = 0
    line: str | None = None
    hub_pattern = re.compile(r'''
        ^(start_hub|end_hub|hub):\s+
        (\S+)\s+
        (-?\d+)\s+
        (-?\d+)
        (?:\s+\[([^\]]*)\])?
        $
    ''', re.VERBOSE)

    conn_pattern = re.compile(r'''
        ^connection:\s+
        (\S+)-(\S+)
        (?:\s+\[([^\]]*)\])?
        $
    ''', re.VERBOSE)

    with open(filename, "r") as f:
        for line_num, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            m = re.fullmatch(r'^nb_drones:\s*(-?\d+)$', stripped)
            if m:
                if nb_drones is None:
                    nb_drones = int(m.group(1))
                    if nb_drones <= 0:
                        raise ParsingError(
                            "can't accept zero/negative values for nb_drones",
                            line_num,
                            line)
                    else:
                        continue
                else:
                    raise ParsingError(
                        "can't allow duplicate for nb_drones",
                        line_num,
                        line)

            if nb_drones is None:
                raise ParsingError("Missing nb_drones", line_num, line)

            m = hub_pattern.fullmatch(stripped)
            if m:
                htype, name, x, y, meta_str = m.groups()
                meta = parse_metadata("zone", meta_str, line_num, line)
                if name in zones:
                    raise ParsingError("duplicate zone name", line_num, line)
                zone_type = models.ZoneType[meta.get("zone", "normal")]
                if htype == "start_hub":
                    if start is None:
                        metadata = models.ZoneMetadata(
                            zone_type,
                            meta.get("color"),
                            meta.get("max_drones", 1)
                        )
                        zones[name] = models.Zone(name, x, y, metadata)
                        start = zones[name]
                    else:
                        raise ParsingError(
                            "start_hub must be unique", line_num, line)
                elif htype == 'end_hub':
                    if end is None:
                        metadata = models.ZoneMetadata(
                            zone_type,
                            meta.get("color"),
                            meta.get("max_drones", 1)
                        )
                        zones[name] = models.Zone(name, x, y, metadata)
                        end = zones[name]

                    else:
                        raise ParsingError(
                            "end_hub must be unique", line_num, line)
                else:
                    metadata = models.ZoneMetadata(
                        zone_type,
                        meta.get("color"),
                        meta.get("max_drones", 1)
                    )
                    zones[name] = models.Zone(name, x, y, metadata)
                continue
            m = conn_pattern.fullmatch(stripped)
            if m:
                z1, z2, meta_str = m.groups()
                raw_conns.append((z1, z2, meta_str, line_num, line))
            
        seen = set()
        for (z1, z2, meta_str, conn_line_num, conn_line) in raw_conns:
            if z1 not in zones or z2 not in zones:
                raise ParsingError("connection references unknown zone", conn_line_num, conn_line)
            key = frozenset((z1, z2))
            if key in seen:
                raise ParsingError("duplicate connection", conn_line_num, conn_line)
            seen.add(key)
            meta = parse_metadata("connection", meta_str, conn_line_num, conn_line)
            conns.append(models.Connection(zones[z1], zones[z2], meta.get("max_link_capacity", 1)))

    if nb_drones is None:
        raise ParsingError("missing nb_drones", None, None)
    if not zones:
        raise ParsingError("no zones defined", None, None)
    if start is None:
        raise ParsingError("missing start hub", None, None)
    if end is None:
        raise ParsingError("missing end hub", None, None)

    return models.Network(nb_drones, start, end, zones, conns)


def parse_metadata(context, meta_str, line_num, line):
    if meta_str is None:
        return {}
    if meta_str.strip() == "":
        raise ParsingError(f"meta data is set but not filled with anything", line_num, line)
    d = {}
    for item in meta_str.split():
        if '=' not in item:
            raise ParsingError(f"meta data must contain value", line_num, line)
        key, val = item.split('=', 1)
        if key == "color":
                d[key] = val
        elif key == "max_drones" or key == "max_link_capacity":
            if key == "max_drones" and context == "zone":
                if val.isdigit() and int(val) > 0:
                     d[key] = int(val)
                else:
                    raise ParsingError("invalid intiger", line_num, line)

            elif key == "max_link_capacity" and context == "connection":
                if val.isdigit() and int(val) > 0:
                     d[key] = int(val)
                else:
                    raise ParsingError("invalid intiger", line_num, line)
            else:
                raise ParsingError(f"{key} is not valid for {context}", line_num, line)

        elif key == "zone":
            if val in (s.name for s in models.ZoneType):
                d[key] = val
            else:
                raise ParsingError("zone choice isn't valid", line_num, line)
        else:
            raise ParsingError("improper metadata", line_num, line)
    return d


# try:
#     # nb_drones, start_hub, end_hub, hubs, connections = parse_file("testmap/easy/02_simple_fork.txt")
#     network = parse_file("testmap/easy/02_simple_fork.txt")
#     # network = parse_file("testmap/hard/02_capacity_hell.txt")

    
#     print(f"start_hub :{network.start}")
#     print()
#     print(f"end_hub :{network.end}")
#     print()
#     print(f"hubs list :{network.zones}")
#     print()
#     print(f"connections list :{network.connections}")
# except ParsingError as e:
#     print(e)