from typing import Dict, Callable, Optional, List

from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
from sharpy.general.component import Component

from .protoss import *
from .terran import *
from .zerg import *
from . import *

from typing import TYPE_CHECKING

from .default_micro_methods import DefaultMicroMethods

if TYPE_CHECKING:
    from sharpy.knowledges import Knowledge
    from sharpy.combat.group_combat_manager import GroupCombatManager


class MicroRules(Component):
    handle_groups_func: Callable[["GroupCombatManager", Point2, MoveType], None]
    init_group_func: Callable[[MicroStep, CombatUnits, Units, List[CombatUnits], MoveType], None]
    group_solve_combat_func: Callable[[MicroStep, Units, Action], Action]
    unit_solve_combat_func: Callable[[MicroStep, Unit, Action], Action]
    ready_to_shoot_func: Callable[[MicroStep, Unit], bool]
    focus_fire_func: Callable[[MicroStep, Unit, Action, Optional[Dict[UnitTypeId, int]]], Action]
    melee_focus_fire_func: Callable[[MicroStep, Unit, Action, Optional[Dict[UnitTypeId, int]]], Action]
    generic_micro: MicroStep

    def __init__(self) -> None:
        super().__init__()
        self.regroup = True
        self.unit_micros: Dict[UnitTypeId, MicroStep] = dict()
        self.regroup_percentage = 0.75
        # How much distance must be between units to consider them to be in different groups, set to 0 for no grouping
        self.own_group_distance = 7
        # In order to avoid exceptions, let's set default generic micro to something.
        self.generic_micro = MicroStep()

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)

        await self.generic_micro.start(knowledge)

        for micro in self.unit_micros.values():
            await micro.start(knowledge)

    def load_default_methods(self):
        self.handle_groups_func = DefaultMicroMethods.handle_groups
        self.init_group_func = DefaultMicroMethods.init_micro_group
        # Pass command
        self.group_solve_combat_func = lambda step, units, current_command: current_command
        # Pass command
        self.unit_solve_combat_func = lambda step, unit, current_command: current_command

        self.ready_to_shoot_func = DefaultMicroMethods.ready_to_shoot

        self.focus_fire_func = DefaultMicroMethods.focus_fire
        self.melee_focus_fire_func = DefaultMicroMethods.melee_focus_fire

    def load_default_micro(self):
        # Micro controllers / handlers
        self.unit_micros[UnitTypeId.DRONE] = MicroWorkers()
        self.unit_micros[UnitTypeId.PROBE] = MicroWorkers()
        self.unit_micros[UnitTypeId.SCV] = MicroWorkers()

        # Protoss
        self.unit_micros[UnitTypeId.ARCHON] = NoMicro()
        self.unit_micros[UnitTypeId.ADEPT] = MicroAdepts()
        self.unit_micros[UnitTypeId.CARRIER] = MicroCarriers()
        self.unit_micros[UnitTypeId.COLOSSUS] = MicroColossi()
        self.unit_micros[UnitTypeId.DARKTEMPLAR] = MicroZerglings()
        self.unit_micros[UnitTypeId.DISRUPTOR] = MicroDisruptor()
        self.unit_micros[UnitTypeId.DISRUPTORPHASED] = MicroPurificationNova()
        self.unit_micros[UnitTypeId.HIGHTEMPLAR] = MicroHighTemplars()
        self.unit_micros[UnitTypeId.OBSERVER] = MicroObservers()
        self.unit_micros[UnitTypeId.ORACLE] = MicroOracles()
        self.unit_micros[UnitTypeId.PHOENIX] = MicroPhoenixes()
        self.unit_micros[UnitTypeId.SENTRY] = MicroSentries()
        self.unit_micros[UnitTypeId.STALKER] = MicroStalkers()
        self.unit_micros[UnitTypeId.WARPPRISM] = MicroWarpPrism()
        self.unit_micros[UnitTypeId.VOIDRAY] = MicroVoidrays()
        self.unit_micros[UnitTypeId.ZEALOT] = MicroZealots()

        # Zerg
        self.unit_micros[UnitTypeId.ZERGLING] = MicroZerglings()
        self.unit_micros[UnitTypeId.ULTRALISK] = NoMicro()
        self.unit_micros[UnitTypeId.OVERSEER] = MicroOverseers()
        self.unit_micros[UnitTypeId.QUEEN] = MicroQueens()
        self.unit_micros[UnitTypeId.RAVAGER] = MicroRavagers()

        self.unit_micros[UnitTypeId.LURKERMP] = MicroLurkers()
        self.unit_micros[UnitTypeId.INFESTOR] = MicroInfestors()
        self.unit_micros[UnitTypeId.SWARMHOSTMP] = MicroSwarmHosts()
        self.unit_micros[UnitTypeId.LOCUSTMP] = NoMicro()
        self.unit_micros[UnitTypeId.LOCUSTMPFLYING] = NoMicro()
        self.unit_micros[UnitTypeId.VIPER] = MicroVipers()

        # Terran
        self.unit_micros[UnitTypeId.HELLIONTANK] = NoMicro()
        self.unit_micros[UnitTypeId.SIEGETANK] = MicroTanks()
        self.unit_micros[UnitTypeId.VIKINGFIGHTER] = MicroVikings()
        self.unit_micros[UnitTypeId.MARINE] = MicroBio()
        self.unit_micros[UnitTypeId.MARAUDER] = MicroBio()
        self.unit_micros[UnitTypeId.BATTLECRUISER] = MicroBattleCruisers()
        self.unit_micros[UnitTypeId.RAVEN] = MicroRavens()
        self.unit_micros[UnitTypeId.MEDIVAC] = MicroMedivacs()
        self.unit_micros[UnitTypeId.LIBERATOR] = MicroLiberators()
        self.unit_micros[UnitTypeId.REAPER] = MicroReaper()
        self.unit_micros[UnitTypeId.WIDOWMINE] = MicroMines()

        self.generic_micro = GenericMicro()
