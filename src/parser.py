import re
from src import models
import matplotlib.colors as mcolors

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


def raise_error(msg, line_num, line):
    raise ParsingError(msg, line_num, line)


def parse_file(filename):
    zones: dict[str, models.Zone] = {} #should be same as raw conns, we fill the data in and them we modify it
    start:          models.Zone | None = None
    end:            models.Zone | None = None
    nb_drones:      int | None = None
    raw_conns:      list[tuple[str, str, int | None, int, str]] = []
                    # (z1, z2, meta_str, line_num, line_content)
    # zonelist: list[str] = []
    connectionlist: list[tuple[str, str]] = []
    # meta: dict[str | None, str | None, int | None] = {}
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
        (?:\s+\[(max_link_capacity=\d+)\])? #replace with \[([^\]]*)\] in future
        $
    ''', re.VERBOSE)


    with open(filename, "r") as f:
        for line_num, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            m = re.fullmatch(r'^nb_drones:\s*(-?\d+)$', stripped)
            if m:
                if nb_drones == None:
                    nb_drones = int(m.group(1))
                    continue
                else:
                    raise ParsingError("can't allow duplicate for number of drones", line_num, line)

            if nb_drones is None:
                raise ParsingError("Missing nb_drones", line_num, line)
            elif nb_drones <= 0:
                raise ParsingError("can't accept zero or negative values for nb_drones", line_num, line)

            m = hub_pattern.fullmatch(stripped)
            if m:
                htype, name, x, y, meta_str = m.groups()
                meta = parse_metadata(meta_str, line_num, line)
                if htype == "start_hub":
                    if start is None:
                        # if meta.get("max_drones")
                        metadata = models.ZoneMetadata(
                            meta.get("zone"), 
                            meta.get("color"),
                            meta.get("max_drones")
                        )
                        print(metadata)
                        # zones = models.Zone(name, x, y, metadata)
                        zones[name] = models.Zone(name, x, y, metadata)
                        start = zones[name]
                        # zonelist.append(name)
                    else:
                        raise ParsingError("start_hub must be unique", line_num, line)
                elif htype == 'end_hub':
                    if end is None:
                        metadata = models.ZoneMetadata(
                            meta.get("zone"), 
                            meta.get("color"), 
                            meta.get("max_drones")
                        )
                        # zones = models.Zone(name, x, y, metadata)
                        zones[name] = models.Zone(name, x, y, metadata)
                        end = models.Zone(name, x, y, metadata)

                        # zonelist.append(name)
                    else:
                        raise ParsingError("end_hub must be unique", line_num, line)
                else: 
                    if name not in zones:
                        metadata = models.ZoneMetadata(
                            meta.get("zone"), 
                            meta.get("color"), 
                            meta.get("max_drones")
                        )
                        # zones = models.Zone(name, x, y, metadata)
                        zones[name] = models.Zone(name, x, y, metadata)

                        # zonelist.append(name)
                    else:
                        raise ParsingError("can't accept hub duplicates", line_num, line)
                continue
            m = conn_pattern.fullmatch(stripped)
            if m:
                z1, z2, meta_str = m.groups()
                if z1 in zones and z2 in zones:
                    if (z1, z2) not in connectionlist and (z2, z1) not in connectionlist:
                        if meta_str:
                            meta = parse_metadata(meta_str, line_num, line)
                            raw_conns.append((z1, z2, meta.get("maxdrones"), line_num, line))
                        else:
                            raw_conns.append((z1, z2, line_num, line))
                        connectionlist.append((z1,z2))
                    else:
                        raise ParsingError("can't accept connection duplicates", line_num, line)
                else:
                    raise ParsingError("need to use existing hubs", line_num, line)
                continue
            raise ParsingError("invalid line", line_num, line)
            

    if line_num == 0 and line == None:
        raise ParsingError("Missing file content", line_num, line)
    elif start is None or end is None:
        raise ParsingError("Missing start or end hub", line_num, line) 
    return nb_drones, start, end, zones, raw_conns


def parse_metadata(meta_str, line_num, line):
    if meta_str is None:
        return {}
    if meta_str.strip() == "":
        if isinstance(meta_str, str):
            raise ParsingError(f"meta data is set but not filled with anything", line_num, line)
        return {}
    d = {}
    for item in meta_str.split():
        if '=' not in item:
            raise ParsingError(f"meta data must contain value", line_num, line)
        key, val = item.split('=', 1)
        if key == "color":
                d[key] = val
        elif key == "max_drones" or key == "max_link_capacity":
            if val is not None and int(val) > 0:
                 d[key] = val
            else:
                raise ParsingError("invalid intiger", line_num, line)
        elif key == "zone":
            # d[key] = val
            # for s in models.ZoneType:
            # if val is ( "normal" or "blocked" or "restricted" or "priority"):
            if val in (s.name for s in models.ZoneType):
                d[key] = val
            else:
                raise ParsingError("zone choice isn't valid", line_num, line)
    return d



try:
    nb_drones, start_hub, end_hub, hubs, connections = parse_file("testmap/easy/02_simple_fork.txt")
    
    print(f"start_hub :{start_hub}")
    print()
    print(f"end_hub :{end_hub}")
    print()
    print(f"hubs list :{hubs}")
    print()
    print(f"connections list :{connections}")  
except ParsingError as e:
    print(e)
