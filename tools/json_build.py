import json
from collections import defaultdict
from typing import List, Set, Optional, Union

from sc2.player import Race
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId


def main():
    build_order = []
    building_count = defaultdict(int)
    unit_count = defaultdict(int)
    with open("build_order.json", "r") as f:
        raw_order = json.load(f)

    race = get_race(raw_order)

    unit_count[UnitTypeId.OVERLORD] = 1

    if race == Race.Protoss:
        worker = UnitTypeId.PROBE
        townhall = UnitTypeId.NEXUS
    elif race == Race.Terran:
        worker = UnitTypeId.SCV
        townhall = UnitTypeId.COMMANDCENTER
    elif race == Race.Zerg:
        unit_count[UnitTypeId.OVERLORD] = 1
        worker = UnitTypeId.DRONE
        townhall = UnitTypeId.HATCHERY
    else:
        print("Unknown race")
        return

    unit_count[worker] = 12
    unit_count[townhall] = 1

    text = ""
    last_line: Optional[str] = None
    last_id: Optional[Union[UnitTypeId, UpgradeId]] = None

    for order in raw_order:
        line = ""

        if order["type"] in {"unit", "structure", "worker"}:
            id = UnitTypeId(order["id"])
            unit_count[id] += 1
            line += f"BuildId({str(id)}, to_count={unit_count[id]})"
        elif order["type"] == "upgrade":
            id = UpgradeId(order["id"])
            line += f"Tech({str(id)})"
        elif order["type"] == "action" and order["name"] == "chronoboost_busy_nexus":
            id = None
            line += "ChronoUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 1)"
        else:
            id = None
            line += "# " + order["name"]

        line += ","

        if last_line is not None and (last_id is None or last_id != id):
            print(last_line)
            text += last_line + "\n"

        last_line = line
        last_id = id

    print(last_line)
    text += last_line + "\n"

    # print(text)


def get_race(raw_order):
    for order in raw_order:
        if order["type"] == "worker" and order["id"] == UnitTypeId.SCV.value:
            return Race.Terran
        if order["type"] == "worker" and order["id"] == UnitTypeId.DRONE.value:
            return Race.Zerg
        if order["type"] == "worker" and order["id"] == UnitTypeId.PROBE.value:
            return Race.Protoss
    return Race.Random


if __name__ == "__main__":
    main()
