import json
from collections import defaultdict
from typing import List, Set, Optional, Union, Dict

from sc2.player import Race
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId


def main():
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

    text_timings = "WarnBuildMacro(["

    text = ""
    last_line: Optional[str] = None
    last_id: Optional[Union[UnitTypeId, UpgradeId]] = None
    replacer_dict = action_replacement_dict()

    for order in raw_order:
        line = ""

        if order["type"] in {"unit", "structure", "worker"}:
            id = UnitTypeId(order["id"])
            unit_count[id] += 1
            line += f"BuildId({str(id)}, to_count={unit_count[id]})"
            if order["type"] == "structure":
                text_timings += f"({str(id)}, {unit_count[id]}, {order['frame'] // 22.4}),"
        elif order["type"] == "upgrade":
            id = UpgradeId(order["id"])
            line += f"Tech({str(id)})"
        elif order["type"] == "action" and order["name"] in replacer_dict:
            id = None
            line += replacer_dict[order["name"]]
        else:
            id = None
            line += "# " + order["name"]

        line += ","

        if last_line is not None and (last_id is None or last_id != id):
            text += last_line + "\n"

        last_line = line
        last_id = id

    text += last_line + "\n"
    text_timings += "], []),"
    print(text_timings)
    print(text)


def action_replacement_dict() -> Dict[str, str]:
    return {
        "chronoboost_busy_nexus": "ChronoBuilding(UnitTypeId.NEXUS, 1)",
        "chronoboost_busy_gateway": "ChronoBuilding(UnitTypeId.GATEWAY, 1)",
        "chronoboost_busy_forge": "ChronoBuilding(UnitTypeId.FORGE, 1)",
        "chronoboost_busy_warpgate": "ChronoBuilding(UnitTypeId.WARPGATE, 1)",
        "chronoboost_busy_cybercore": "ChronoBuilding(UnitTypeId.CYBERNETICSCORE, 1)",
        "chronoboost_busy_robo": "ChronoBuilding(UnitTypeId.ROBOTICSFACILITY, 1)",
        "chronoboost_busy_stargate": "ChronoBuilding(UnitTypeId.STARGATE, 1)",
        "chronoboost_busy_twilight": "ChronoBuilding(UnitTypeId.TWILIGHTCOUNCIL, 1)",
    }


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
