"""
# Ontology: app.game.mechanics

Package for Mechanic implementations.
"""
# Standard Libraries
from __future__ import annotations
from typing import TYPE_CHECKING

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board

from app.config.enums import (
    AssetCategories, 
    AssetInstances,
    Intentions,
)
from app.game.logic.mechanics import Mechanic

# Cython Libraries
from libs.core.math import (
    Geometry, 
    Physics, 
    Space
)

# ----------------------------------------------------------------------------------------

class SpatialMechanic(Mechanic):
    """
    ## SpatialMechanic

    Base mechanic for systems requiring broad-phase spatial hashing and geometry resolution.
    """
    
    grid: Space

    def __init__(self, cell_size: int = 64, max_entities: int = 2000):
        # Allocated exactly once in memory during orchestration
        self.grid = Space(cell_size=cell_size, max_entities=max_entities)

    def query_collisions(self, assets: list) -> list[tuple]:
        """
        Extracts primitives, queries the C-grid, and returns colliding Asset pairs.
        """
        self.grid.clear()
        
        if not assets:
            return []

        asset_map = dict(enumerate(assets))
        primitive_data = [asset.primitive(i) for i, asset in enumerate(assets)]
        
        colliding_indices = Physics.collisions(primitive_data, self.grid)
        return [(asset_map[id_a], asset_map[id_b]) for id_a, id_b in colliding_indices]
    
# ----------------------------------------------------------------------------------------

class SwitchMechanics(SpatialMechanic):
    """
    ## SwitchMechanics

    Mechanic responsible for triggering plates and linking their states to gates.
    """

    def __init__(self):
        super().__init__(max_entities=1000)

    def update(self, board: Board, delta_time: float) -> None:
        """
        """
        for layer in board.layers():
            plates = board.instances(AssetInstances.PLATES, layer)
            if not plates:
                continue
                
            crates = board.instances(AssetInstances.CRATES, layer)
            gates = board.instances(AssetInstances.GATES, layer)
            sheets = board.categories(AssetCategories.SHEETS, layer)

            colliding_pairs = self.query_collisions(plates + crates + sheets)

            pressed_plates = set()

            for asset_a, asset_b in colliding_pairs:
                is_a_plate = asset_a.taxonomy.instance == AssetInstances.PLATES
                is_b_plate = asset_b.taxonomy.instance == AssetInstances.PLATES

                # Filter: Only care if exactly one is a plate
                if is_a_plate and not is_b_plate:
                    plate, weight = asset_a, asset_b
                elif is_b_plate and not is_a_plate:
                    plate, weight = asset_b, asset_a
                else:
                    continue

                # Validate the overlapping entity is a valid weight
                if (weight.taxonomy.instance == AssetInstances.CRATES or 
                    weight.taxonomy.category == AssetCategories.SHEETS):
                    pressed_plates.add(plate)

            # Apply State and Notify Gates
            for plate in plates:
                is_pressed = plate in pressed_plates
                
                # Check if the state has mutated this frame
                if plate.state.switch != is_pressed:
                    plate.state.switch = is_pressed
                    
                    # Synchronize linked gates
                    for gate in gates:
                        if gate.state.link == plate.state.link:
                            gate.state.switch = plate.state.switch
                            
# ----------------------------------------------------------------------------------------

class ProjectileMechanics(SpatialMechanic):
    """
    ## ProjectileMechanics

    Mechanic responsible for tracking projectile trajectories and impacts.
    """

    def __init__(self):
        super().__init__(max_entities=1000)

    def update(self, board: Board, delta_time: float) -> None:
        """
        """
        for layer in board.layers():
            projectiles = board.instances(AssetInstances.PROJECTILES, layer)
            if not projectiles:
                continue
                
            sheets = board.categories(AssetCategories.SHEETS, layer)
            
            colliding_pairs = self.query_collisions(projectiles + sheets)

            for asset_a, asset_b in colliding_pairs:
                # Filter out sheet-sheet and proj-proj collisions 
                is_a_proj = asset_a.taxonomy.instance == AssetInstances.PROJECTILES
                is_b_proj = asset_b.taxonomy.instance == AssetInstances.PROJECTILES

                if is_a_proj and not is_b_proj:
                    proj, target = asset_a, asset_b
                elif is_b_proj and not is_a_proj:
                    proj, target = asset_b, asset_a
                else:
                    continue

                # TODO: Resolve projectile impact (e.g., mark proj for GC, apply damage to target)
                pass

# ----------------------------------------------------------------------------------------

class CollisionMechanics(SpatialMechanic):
    """
    ## CollisionMechanics

    Mechanic responsible for resolving Asset collisions natively.
    """

    def __init__(self):
        super().__init__(max_entities=2000)

    def update(self, board: Board, delta: float) -> None:
        """
        ### update(board, delta)

        Resolves kinematic overlap constraints using the broad-phase physics pipeline.
        """
        for layer in board.layers():
            dynamic_assets = (
                board.instances(AssetInstances.SPRITES, layer) +
                board.instances(AssetInstances.PLAYERS, layer) +
                board.instances(AssetInstances.CRATES, layer)
            )

            colliding_pairs = self.query_collisions(dynamic_assets)
            
            for asset_a, asset_b in colliding_pairs:
                # Setup trigger interactions
                if hasattr(asset_a.state, 'mutators') and hasattr(asset_a.state.mutators, 'triggers'):
                    asset_a.state.mutators.triggers.struck = True
                if hasattr(asset_b.state, 'mutators') and hasattr(asset_b.state.mutators, 'triggers'):
                    asset_b.state.mutators.triggers.struck = True

                # Calculate centers
                cx_a = asset_a.state.position.x + (asset_a.dimensions.w / 2)
                cy_a = asset_a.state.position.y + (asset_a.dimensions.l / 2)
                cx_b = asset_b.state.position.x + (asset_b.dimensions.w / 2)
                cy_b = asset_b.state.position.y + (asset_b.dimensions.l / 2)

                dx = cx_b - cx_a
                dy = cy_b - cy_a

                if dx == 0 and dy == 0:
                    dx = 1

                # Resolve spatial overlap
                overlap_x = (asset_a.dimensions.w / 2 + asset_b.dimensions.w / 2) - abs(dx)
                overlap_y = (asset_a.dimensions.l / 2 + asset_b.dimensions.l / 2) - abs(dy)

                if overlap_x > 0 and overlap_y > 0:
                    # Push along the shallowest axis of penetration
                    if overlap_x < overlap_y:
                        shift = int(overlap_x / 2) + 1
                        if dx > 0:
                            asset_a.state.position.x -= shift
                            asset_b.state.position.x += shift
                        else:
                            asset_a.state.position.x += shift
                            asset_b.state.position.x -= shift
                    else:
                        shift = int(overlap_y / 2) + 1
                        if dy > 0:
                            asset_a.state.position.y -= shift
                            asset_b.state.position.y += shift
                        else:
                            asset_a.state.position.y += shift
                            asset_b.state.position.y -= shift

# ----------------------------------------------------------------------------------------

class CombatMechanics(SpatialMechanic):
    """
    """
    def __init__(self):
        super().__init__(max_entities=2000)

    def update(self, board: Board, delta: float) -> None:
        """
        Resolves attack overlaps, decrements health, and triggers mutators.
        """
        # Gather all attacking entities
        attackers = [
            asset for asset in board.instances(AssetInstances.PLAYERS) + board.instances(AssetInstances.SPRITES)
            if asset.state.intention == Intentions.ATTACK.value
        ]

        for attacker in attackers:
            # Determine effective hitboxes (fallback to base asset hitboxes if unarmed)
            active_hitboxes = attacker.hitboxes
            
            if getattr(attacker.state, 'inventory', None) and getattr(attacker.state.inventory, 'equipment', None):
                weapon_key = attacker.state.inventory.equipment.weapon
                if weapon_key and weapon_key in board.equipment.weapons:
                    weapon_props = board.equipment.weapons[weapon_key]
                    if weapon_props.hitboxes:
                        active_hitboxes = weapon_props.hitboxes

            # Gather targets on the same layer
            layer = attacker.state.layer
            targets = board.instances(AssetInstances.SPRITES, layer) + board.instances(AssetInstances.PLAYERS, layer)

            for target in targets:
                if attacker.name == target.name or target.state.mutators.triggers.dead:
                    continue

                if Geometry.intersects(
                    attacker.state.position, 
                    attacker.dimensions, 
                    active_hitboxes,
                    target.state.position, 
                    target.dimensions, 
                    target.hitboxes
                ):
                    # Calculate and apply damage
                    damage = attacker.state.character.strength - target.state.character.defense
                    damage = max(1, damage)  # Minimum 1 damage on hit
                    
                    target.state.meters.health.current = max(0, target.state.meters.health.current - damage)
                    target.state.mutators.triggers.struck = True
                    
                    if target.state.meters.health.current == 0:
                        target.state.mutators.triggers.dead = True