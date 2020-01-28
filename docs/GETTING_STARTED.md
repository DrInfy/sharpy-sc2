# Getting started...

Refer to the [dummy bots](../dummies/) for examples on how to do things.

Specifically [macro_stalkers.py](../dummies/protoss/macro_stalkers.py) is a good start.

## `create_plan`
The `create_plan` method is where you define what actions you want your bot to take throughout the game. Here you return a `BuildOrder` containing said actions.
  
**It's important to understand that, despite the name, this is not just a build order** - it also contains attack plans, worker management, and much more!

It's also important to understand that each step in a given build order is executed in parallel (all at the same time). If you want them to happen one after the other, contain them in a `SequentialList`.

Parallel example:
```python
    async def create_plan(self) -> BuildOrder:
        return BuildOrder([
            Step1,
            Step2,
            Step3
        ])
```
Step 1, 2 and 3 are all executed simultaneous.

Sequential example:
```python
    async def create_plan(self) -> BuildOrder:
        return BuildOrder([
            SequentialList([
                Step1,
                Step2,
                Step3
            ])
        ])
```
Step 1, 2 and 3 are all executed in the order they are listed - one after the other.



Using the [macro_stalkers.py](../dummies/protoss/macro_stalkers.py) dummy bot as an example, we see the following:
```python
    async def create_plan(self) -> BuildOrder:
        return BuildOrder([
            Step(None, ChronoUnitProduction(UnitTypeId.PROBE, UnitTypeId.NEXUS),
                 skip=RequiredUnitExists(UnitTypeId.PROBE, 40, include_pending=True), skip_until=RequiredUnitExists(UnitTypeId.ASSIMILATOR, 1)),
            SequentialList([
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 14),
                GridBuilding(UnitTypeId.PYLON, 1),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 16),
                StepBuildGas(1),
                GridBuilding(UnitTypeId.GATEWAY, 1),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 20),
                ActExpand(2),
                # Removed for brevity
            ]),
            SequentialList([
                PlanZoneDefense(),
                RestorePower(),
                PlanDistributeWorkers(),
                PlanZoneGather(),
                Step(RequiredUnitReady(UnitTypeId.GATEWAY, 4), PlanZoneAttack(4)),
                PlanFinishEnemy(),
            ])
        ]),
```

Here the first `Step` and two `SequentialList` steps will operate in parallel, but the items inside each `SequentialList` will happen in the order they're listed.

##### First step:
```python
Step(None, ChronoUnitProduction(UnitTypeId.PROBE, UnitTypeId.NEXUS),
                 skip=RequiredUnitExists(UnitTypeId.PROBE, 40, include_pending=True), skip_until=RequiredUnitExists(UnitTypeId.ASSIMILATOR, 1)),
```
This step manages the chrono boosting of probe production. Because it's run in parallel, it means it will operate throughout the game.  
- `ChronoUnitProduction(UnitTypeId.PROBE, UnitTypeId.NEXUS)`  
Cast Chrono boost on any probes being made at a nexus.  
- `skip_until=RequiredUnitExists(UnitTypeId.ASSIMILATOR, 1)`  
Skip this step until the bot has an assimilator.  
- `RequiredUnitExists(UnitTypeId.PROBE, 40, include_pending=True)`  
Skip this step once the bot has 40 probes (including any currently being produced).  

##### Second step:
```python
            SequentialList([
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 14),
                GridBuilding(UnitTypeId.PYLON, 1),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 16),
                StepBuildGas(1),
                GridBuilding(UnitTypeId.GATEWAY, 1),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 20),
                ActExpand(2),
                # Removed for brevity
            ]),
```
This `SequentialList` step will move through the steps that create the bot's production and units.
- `ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 14)`  
Create probes from the Nexus up to a total count of 14 probes.  
- `GridBuilding(UnitTypeId.PYLON, 1)`  
Create pylons up to a total count of 1. i.e. it creates a single pylon. 
- `ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 16)`  
Create probes from the Nexus up to a total count of 16 probes. 
- `StepBuildGas(1)`  
Create gas buildings up to a total count of 1. i.e. it builds a single assimilator.
- `GridBuilding(UnitTypeId.GATEWAY, 1)`  
Create gateways up to a total count of 1. i.e. it builds a single gateway.
- `ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 20)`  
Create probes from the Nexus up to a total count of 20 probes. 
- `ActExpand(2)`  
Create bases up to a total count of 2. i.e. we already have a main base, so build 1 more.

##### Third step:
```python
            SequentialList([
                PlanZoneDefense(),
                RestorePower(),
                PlanDistributeWorkers(),
                PlanZoneGather(),
                Step(RequiredUnitReady(UnitTypeId.GATEWAY, 4), PlanZoneAttack(4)),
                PlanFinishEnemy(),
            ])
```
This `SequentialList` step will perform a number of 'house keeping' duties, as well as managing the execution of an attack once the bot has a total of 4 gateways.
- `PlanZoneDefense()`  
Manage defending our base/etc
- `RestorePower()`  
Build a pylon next to any de-powered buildings
- `PlanDistributeWorkers()`  
Handle idle workers and worker distribution
- `PlanZoneGather()`  
Manage where our units gather
- `Step(RequiredUnitReady(UnitTypeId.GATEWAY, 4), PlanZoneAttack(4))`  
Attack the enemy once the bot has 4 gateways built
- `PlanFinishEnemy()`  
Finish the attack
