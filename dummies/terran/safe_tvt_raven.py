from sc2 import UnitTypeId, Race, Result
from sc2.ids.upgrade_id import UpgradeId
from sc2.ids.ability_id import AbilityId
from sc2.bot_ai import BotAI

from sharpy.knowledges import KnowledgeBot, Knowledge
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sharpy.plans.acts import *
from sharpy.plans.acts.terran import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *

from sharpy.plans.tactics.terran import CallMule, LowerDepots
from sharpy.plans.tactics.terran.addon_swap import PlanAddonSwap, ExecuteAddonSwap


class TerranSafeTvT(KnowledgeBot):
    """
    TvT Safe Opening
    Double gas 3 reaper 2 hellion opening
    Leave 4/6 in gas, factory expand
    Reactor on rax, techlab on factory - after cyclone, swap with starport to make 2-3 raven, then reactored vikings and tanks
    3rd cc at 4:00 to 5:00
    Then +2 rax
    Then +2 ebays
    Then +2 rax
    """

    def __init__(self):
        super().__init__("Safe TvT Raven Opening")

    async def create_plan(self) -> BuildOrder:
        scv = [
            Step(None, TerranUnit(UnitTypeId.SCV, 14), skip=UnitExists(UnitTypeId.SUPPLYDEPOT)),
            Step(None, TerranUnit(UnitTypeId.SCV, 15), skip=UnitReady(UnitTypeId.SUPPLYDEPOT)),
            Step(None, TerranUnit(UnitTypeId.SCV, 19), skip=UnitReady(UnitTypeId.BARRACKS)),
            BuildOrder(
                Step(UnitReady(UnitTypeId.BARRACKS, 1), MorphOrbitals()),
                Step(
                    None,
                    ActUnit(UnitTypeId.SCV, UnitTypeId.COMMANDCENTER, 16 + 6),
                    skip=UnitExists(UnitTypeId.COMMANDCENTER, 2),
                ),
                Step(None, ActUnit(UnitTypeId.SCV, UnitTypeId.COMMANDCENTER, 3 * 22)),
            ),
        ]

        gas_management = [
            # Mine with 6 workers until first barracks is complete
            Step(None, DistributeWorkers(6), skip=UnitReady(UnitTypeId.BARRACKS)),
            # Mine with 4 workers until the natural CC is started
            Step(
                None,
                DistributeWorkers(4, 4),
                skip_until=UnitReady(UnitTypeId.BARRACKS),
                skip=UnitExists(UnitTypeId.COMMANDCENTER, 2),
            ),
            # Mine with at least 9 workers afterwards
            Step(None, DistributeWorkers(min_gas=9), skip_until=UnitExists(UnitTypeId.COMMANDCENTER, 2)),
        ]

        units = [
            Step(
                UnitExists(UnitTypeId.FACTORY, include_pending=True),
                BuildOrder(
                    TerranUnit(UnitTypeId.REAPER, 3, only_once=True), TerranUnit(UnitTypeId.HELLION, 2, only_once=True),
                ),
            ),
            BuildOrder(
                TerranUnit(UnitTypeId.CYCLONE, 1, only_once=True),
                TerranUnit(UnitTypeId.RAVEN, 2, only_once=True),
                Step(
                    UnitExists(UnitTypeId.CYCLONE, include_killed=True),
                    TerranUnit(UnitTypeId.SIEGETANK, 5, only_once=True),
                ),
                Step(
                    UnitExists(UnitTypeId.RAVEN, 2, include_killed=True),
                    TerranUnit(UnitTypeId.VIKINGFIGHTER, 6, only_once=True),
                ),
            ),
            # Late game units
            BuildOrder(
                TerranUnit(UnitTypeId.MARINE, 100),
                TerranUnit(UnitTypeId.SIEGETANK, 10),
                [
                    TerranUnit(UnitTypeId.MEDIVAC, 4),
                    TerranUnit(UnitTypeId.VIKINGFIGHTER, 6),
                    TerranUnit(UnitTypeId.LIBERATOR, 2),
                    TerranUnit(UnitTypeId.VIKINGFIGHTER, 20),
                ],
            ),
        ]

        research = [
            Tech(UpgradeId.STIMPACK),
            Tech(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1),
            Tech(UpgradeId.TERRANINFANTRYARMORSLEVEL1),
            Tech(UpgradeId.SHIELDWALL),
            Tech(UpgradeId.TERRANVEHICLEWEAPONSLEVEL1),
            Tech(UpgradeId.TERRANINFANTRYWEAPONSLEVEL2),
            Tech(UpgradeId.TERRANINFANTRYARMORSLEVEL2),
            Tech(UpgradeId.TERRANVEHICLEWEAPONSLEVEL2),
            Tech(UpgradeId.TERRANINFANTRYWEAPONSLEVEL3),
            Tech(UpgradeId.TERRANINFANTRYARMORSLEVEL3),
            Tech(UpgradeId.TERRANVEHICLEWEAPONSLEVEL3),
            Tech(UpgradeId.TERRANSHIPWEAPONSLEVEL1),
            Tech(UpgradeId.TERRANSHIPWEAPONSLEVEL2),
            Tech(UpgradeId.TERRANSHIPWEAPONSLEVEL3),
            # TODO Fix me, doesn't work in python-sc2 and neither does here:
            # Tech(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL1),
            # Tech(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL2),
            # Tech(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL3),
        ]

        mid_game_addons = Step(
            None,
            BuildOrder(
                # Rebuild addons
                BuildAddon(UnitTypeId.BARRACKSREACTOR, UnitTypeId.BARRACKS, 5),
                BuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 2),
                BuildAddon(UnitTypeId.STARPORTREACTOR, UnitTypeId.STARPORT, 1),
            ),
            skip_until=UnitExists(UnitTypeId.BARRACKS, 2, include_not_ready=False),
        )

        addon_swap = [
            # Addon count before 3rd cc is placed
            Step(
                None,
                PlanAddonSwap(barracks_reactor_count=1, factory_techlab_count=1, starport_techlab_count=1),
                skip=UnitExists(UnitTypeId.COMMANDCENTER, 3, include_killed=True, include_pending=True),
            ),
            # Once the 2 ravens are out, swap addons to allow reactored viking production and stim research
            Step(
                None,
                PlanAddonSwap(barracks_techlab_count=1, factory_techlab_count=1, starport_reactor_count=1),
                skip_until=UnitExists(UnitTypeId.RAVEN, 2, include_killed=True),
                skip=UnitExists(UnitTypeId.BARRACKS, 5, include_killed=True),
            ),
            Step(
                None,
                PlanAddonSwap(
                    barracks_techlab_count=1,
                    barracks_reactor_count=4,
                    factory_techlab_count=1,
                    starport_reactor_count=1,
                ),
                skip_until=UnitExists(UnitTypeId.BARRACKS, 5, include_killed=True),
                skip=TechReady(UpgradeId.SHIELDWALL),
            ),
            # Once stim and combatshield is researched, have a 5-2-1 setup
            Step(
                None,
                PlanAddonSwap(
                    barracks_reactor_count=5, factory_techlab_count=2, starport_reactor_count=1, only_once=False
                ),
                skip_until=TechReady(UpgradeId.SHIELDWALL),
            ),
        ]

        return BuildOrder(
            # Handle all scv production
            scv,
            # Handle gas saturation
            gas_management,
            # Handle addon swapping
            addon_swap,
            ExecuteAddonSwap(),
            # Addon (re-)building
            mid_game_addons,
            # Handle all unit production
            units,
            # Build structures
            [
                Step(Supply(14), GridBuilding(UnitTypeId.SUPPLYDEPOT, 1),),
                BuildGas(1),
                GridBuilding(UnitTypeId.BARRACKS, 1),
                StepBuildGas(2, requirement=Supply(17)),
                GridBuilding(UnitTypeId.FACTORY, 1),
                GridBuilding(UnitTypeId.SUPPLYDEPOT, 2),
                # Expand should start at around 2:28
                Expand(2, priority=True),
                GridBuilding(UnitTypeId.SUPPLYDEPOT, 3),
                GridBuilding(UnitTypeId.STARPORT, 1),
                BuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 1),
                # TODO Unsure how to handle only building this addon once? Need a 'only_once' for BuildAddon
                Step(
                    None,
                    BuildAddon(UnitTypeId.BARRACKSTECHLAB, UnitTypeId.BARRACKS, 1),
                    skip=UnitReady(UnitTypeId.FACTORYTECHLAB),
                ),
                # Third gas at natural should be started at 3:20 before the CC finishes
                BuildGas(3),
                # At around 4:20, this command center should be placed in-base and flown out later
                # TODO Build 3rd CC inbase if possible
                Step(Time(4 * 60 + 20), Expand(3),),
                AutoDepot(),
                Step(
                    UnitExists(UnitTypeId.RAVEN, 2, include_pending=True),
                    BuildAddon(UnitTypeId.BARRACKSREACTOR, UnitTypeId.BARRACKS, 1),
                    skip=UnitExists(UnitTypeId.RAVEN, 2),
                ),
                Step(
                    UnitExists(UnitTypeId.VIKINGFIGHTER, 2, include_pending=True), GridBuilding(UnitTypeId.BARRACKS, 3),
                ),
                Step(
                    UnitExists(UnitTypeId.VIKINGFIGHTER, 4, include_pending=True),
                    GridBuilding(UnitTypeId.ENGINEERINGBAY, 2),
                ),
                BuildOrder(
                    StepBuildGas(6, skip=All(Gas(200), UnitExists(UnitTypeId.BARRACKS, 5))),
                    Step(
                        UnitExists(UnitTypeId.VIKINGFIGHTER, 6, include_pending=True),
                        GridBuilding(UnitTypeId.BARRACKS, 5),
                    ),
                    # Add 2nd factory when combatshield is nearly done
                    Step(TechReady(UpgradeId.SHIELDWALL, 0.6), GridBuilding(UnitTypeId.FACTORY, 2),),
                    # Add armory when +1 attack is nearly done
                    Step(
                        TechReady(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1, 0.6),
                        GridBuilding(UnitTypeId.ARMORY, 1, priority=True,),
                    ),
                    # Research upgrades
                    research,
                ),
            ],
            CallMule(50),
            LowerDepots(),
            [
                PlanZoneGather(),
                PlanZoneDefense(),
                Step(TechReady(UpgradeId.STIMPACK), PlanZoneAttack(4)),
                PlanFinishEnemy(),
            ],
        )


class LadderBot(TerranSafeTvT):
    @property
    def my_race(self):
        return Race.Terran
