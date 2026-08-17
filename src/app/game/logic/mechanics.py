"""
# Ontology: app.game.mechanics

Package for Mechanic implementations.
"""
# Standard Libraries
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

# Application Libraries
if TYPE_CHECKING:
    from app.game.board import Board

from app.config.enums import (
    AssetCategories, 
    AssetInstances,
    Intentions,
    PlayerGoals,
    GoalCategories
)
from app.game.logic.maps import (
    AnimationMap
)
from app.models.state import (
    Goal,
    SpriteState
)

# Cython Libraries
from libs.core.models import Position
from libs.core.math import (
    Geometry, 
    Physics, 
    Space
)

# ----------------------------------------------------------------------------------------

class Mechanic(ABC):
    """
    ## Mechanic

    Foundational class for game Mechanics. Defines the `update()` interface used by the Engine.
    """

    @abstractmethod 
    def update(self, board: Board, delta: float) -> None:
        """
        ### update(board, delta)

        Engine interface. Injects:

        - board: Game Board
        - delta: Time Delta
        """
        pass

# ----------------------------------------------------------------------------------------

class AnimationMechanics(Mechanic):
    """
    ## AnimationMechanics

    Mechanic responsible for animating Assets.
    """

    def update(self, board: Board, delta: float) -> None:
        """
        ### update(board, delta)

        Iterates over animate Asset and injects state and property data into their Animation interface.
        """
        for asset in board.categories(AssetCategories.EFFECTS):
            asset.animation.animate(asset.state, asset.properties)
        for asset in board.categories(AssetCategories.SHEETS):
            asset.animation.animate(asset.state, asset.properties)
        for asset in board.instances(AssetInstances.CHESTS):
            asset.animation.animate(asset.state, asset.properties)
        for asset in board.instances(AssetInstances.GATES):
            asset.animation.animate(asset.state, asset.properties)
        for asset in board.instances(AssetInstances.PLATES):
            asset.animation.animate(asset.state, asset.properties)

# ----------------------------------------------------------------------------------------

class CollisionMechanics(Mechanic):
    """
    ## CollisionMechanics

    Mechanic responsible for resolving Asset collisions natively.
    """

    def __init__(self):
        # Allocated exactly once in memory during orchestration to avoid heap-allocation overheads 
        self.grid = Space(cell_size=64, max_entities=2000)

    def update(self, board: Board, delta: float) -> None:
        """
        ### update(board, delta)

        Extracts primitive properties from Assets, partitions them spatially, and 
        resolves kinematic overlap constraints.
        """
        # Zero out the underlying C-array for this frame
        self.grid.clear()

        for layer in board.layers():
            # 1. Gather dynamic assets on the current layer
            dynamic_assets = (
                board.instances(AssetInstances.SPRITES, layer) +
                board.instances(AssetInstances.PLAYERS, layer) +
                board.instances(AssetInstances.CRATES, layer)
            )

            asset_map = {}
            primitive_data = []

            # 2. Extract and flatten spatial data into primitives
            for i, asset in enumerate(dynamic_assets):
                asset_map[i] = asset
                
                # Fetch spatial and dimensional state natively
                x = asset.state.position.x if asset.state.position else 0
                y = asset.state.position.y if asset.state.position else 0
                w = asset.dimensions.w if asset.dimensions else 0
                l = asset.dimensions.l if asset.dimensions else 0
                
                # Retrieve standard hitboxes
                hitboxes = asset.hitboxes

                primitive_data.append((i, x, y, w, l, hitboxes))

            # 3. Offload detection natively
            colliding_pairs = Physics.collisions(primitive_data, self.grid)
            
            # 4. Implement Physics & State Resolution 
            for id_a, id_b in colliding_pairs:
                asset_a = asset_map[id_a]
                asset_b = asset_map[id_b]

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

class ProjectileMechanics(Mechanic):
    """
    ## ProjectileMechanics

    Mechanic responsible for tracking projectile trajectories and impacts.
    """

    def __init__(self):
        # Allocated exactly once in memory during orchestration
        self.grid = Space(cell_size=64, max_entities=1000)

    def update(self, board: Board, delta_time: float) -> None:
        """
        Extracts primitive properties from projectiles and targets, partitions them spatially, and resolves overlap.
        """
        # Zero out the underlying C-array for this frame
        self.grid.clear()

        for layer in board.layers():
            projectiles = board.instances(AssetInstances.PROJECTILES, layer)
            
            # Fast exit: Skip spatial hashing entirely if there are no projectiles on this layer
            if not projectiles:
                continue
                
            sheets = board.categories(AssetCategories.SHEETS, layer)
            dynamic_assets = projectiles + sheets

            asset_map = {}
            primitive_data = []

            # 1. Extract and flatten spatial data into primitives
            for i, asset in enumerate(dynamic_assets):
                asset_map[i] = asset
                
                x = asset.state.position.x if asset.state.position else 0
                y = asset.state.position.y if asset.state.position else 0
                w = asset.dimensions.w if asset.dimensions else 0
                l = asset.dimensions.l if asset.dimensions else 0
                
                primitive_data.append((i, x, y, w, l, asset.hitboxes))

            # 2. Offload detection natively
            colliding_pairs = Physics.collisions(primitive_data, self.grid)

            # 3. State Resolution
            for id_a, id_b in colliding_pairs:
                asset_a = asset_map[id_a]
                asset_b = asset_map[id_b]

                # Filter out sheet-sheet and proj-proj collisions 
                # (sheet-sheet collisions are handled natively by CollisionMechanics)
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

class RemoveMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta_time: float) -> None: 
        """
        Garbage collection for expired temporary effects and dead sprites.
        """            
        removals = []

        # 1. Identify expired Temporary Effects
        for effect in board.instances(AssetInstances.TEMPORARY):
            if effect.state.animation.frame >= effect.properties.count:
                removals.append(effect)
                
        # 2. Identify Dead Sprites
        for sprite in board.instances(AssetInstances.SPRITES):
            if sprite.state.mutators.triggers.dead:
                removals.append(sprite)

        # 3. Identify expired Projectiles
        # TODO

        # 4. Safely evict from Board tracking caches
        board.remove(removals)

# ----------------------------------------------------------------------------------------

class SwitchMechanics(Mechanic):
    """
    ## SwitchMechanics

    Mechanic responsible for triggering plates and linking their states to gates.
    """

    def __init__(self):
        # Allocated exactly once in memory during orchestration
        self.grid = Space(cell_size=64, max_entities=1000)

    def update(self, board: Board, delta_time: float) -> None:
        """
        Extracts primitive properties from plates, crates, and sheets,
        partitions them spatially, and resolves switch triggers natively.
        """
        self.grid.clear()

        for layer in board.layers():
            plates = board.instances(AssetInstances.PLATES, layer)
            
            # Fast exit: Skip spatial hashing entirely if there are no plates on this layer
            if not plates:
                continue
                
            crates = board.instances(AssetInstances.CRATES, layer)
            gates = board.instances(AssetInstances.GATES, layer)
            sheets = board.categories(AssetCategories.SHEETS, layer)

            dynamic_assets = plates + crates + sheets

            asset_map = {}
            primitive_data = []

            # 1. Extract and flatten spatial data into primitives
            for i, asset in enumerate(dynamic_assets):
                asset_map[i] = asset
                
                x = asset.state.position.x if asset.state.position else 0
                y = asset.state.position.y if asset.state.position else 0
                w = asset.dimensions.w if asset.dimensions else 0
                l = asset.dimensions.l if asset.dimensions else 0
                
                primitive_data.append((i, x, y, w, l, asset.hitboxes))

            # 2. Offload detection natively
            colliding_pairs = Physics.collisions(primitive_data, self.grid)

            # 3. State Resolution
            pressed_plates = set()

            for id_a, id_b in colliding_pairs:
                asset_a = asset_map[id_a]
                asset_b = asset_map[id_b]

                is_a_plate = asset_a.taxonomy.instance == AssetInstances.PLATES
                is_b_plate = asset_b.taxonomy.instance == AssetInstances.PLATES

                # Filter: Only care if exactly one is a plate
                if is_a_plate and not is_b_plate:
                    plate, weight = asset_a, asset_b
                elif is_b_plate and not is_a_plate:
                    plate, weight = asset_b, asset_a
                else:
                    continue

                # Validate the overlapping entity is a valid weight (Crate or Sheet)
                if (weight.taxonomy.instance == AssetInstances.CRATES or 
                    weight.taxonomy.category == AssetCategories.SHEETS):
                    pressed_plates.add(plate)

            # 4. Apply State and Notify Gates
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

class TransitionMechanics(Mechanic):
    """
    """
    
    def update(self, board: Board, delta: float) -> None:
        """
        Evaluates Intention condition lambdas for state transitions.
        """
        sprites = board.instances(AssetInstances.SPRITES)

        for sprite in sprites:
            # TODO (Phase V): Intention logic and DSL matrix compilation is pending.

            sprite.state.animation.action = AnimationMap.action(
                sprite.state,
                board.equipment
            )
            
            if sprite.state.goal:
                sprite.state.animation.direction = AnimationMap.direction(
                    sprite.state.position,
                    sprite.state.goal.position
                )

            # Query configuration Intentions using the Sprite's actual Intention State
            if sprite.state.intention not in board.configurations.intentions:
                continue

            transits = board.configurations.intentions[sprite.state.intention]
            
            # 2. Evaluate conditions
            for transit in transits:
                if transit.conditions:
                    for condition in transit.conditions:
                        if condition(sprite, board):
                            # 3. Transition the state
                            sprite.state.intention = transit.next
                            
                            # Break immediately to avoid evaluating the NEW state's 
                            # transitions in this same frame.
                            break

# ----------------------------------------------------------------------------------------

class PlayerMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta: float) -> None:
        """
        """
        player = board.player()
        poll = board.poll()
        
        if poll.intentions:
            player.state.intention = poll.intentions[0]
        else:
            player.state.intention = Intentions.IDLE.value
        
        speed = player.state.character.speed
        goal_x = player.state.position.x
        goal_y = player.state.position.y
        
        # Track movement so the player doesn't instantly snap back to 'UP' when inputs are released.
        has_movement = False

        if PlayerGoals.UP.value in poll.goals:
            goal_y -= speed
            has_movement = True
        if PlayerGoals.DOWN.value in poll.goals:
            goal_y += speed
            has_movement = True
        if PlayerGoals.LEFT.value in poll.goals:
            goal_x -= speed
            has_movement = True
        if PlayerGoals.RIGHT.value in poll.goals:
            goal_x += speed
            has_movement = True

        # Initialize missing goal tracking state
        if has_movement and not player.state.goal:
            player.state.goal = Goal(
                name=player.name, 
                category=GoalCategories.POSITION.value, 
                position=Position(goal_x, goal_y)
            )
        elif player.state.goal:
            player.state.goal.position.x = goal_x
            player.state.goal.position.y = goal_y

        if player.state.intention == Intentions.ATTACK.value:
            player.state.mutators.triggers.animated = True
        else:
            player.state.mutators.triggers.animated = has_movement

        player.state.animation.action = AnimationMap.action(
            player.state, 
            board.equipment
        )

        if player.state.goal and has_movement:
            player.state.animation.direction = AnimationMap.direction(
                player.state.position,
                player.state.goal.position
            )
# ----------------------------------------------------------------------------------------

class MotionMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta: float) -> None:
        """
        Iterates over mutable entities and applies vectors based on speed offsets to reach their goals.
        """
        sprites = board.instances(AssetInstances.SPRITES)
        players = board.instances(AssetInstances.PLAYERS)

        for asset in sprites + players:
            if not asset.state.goal:
                continue

            dx = asset.state.goal.position.x - asset.state.position.x
            dy = asset.state.goal.position.y - asset.state.position.y

            # Entity has reached its exact target coordinate destination
            if dx == 0 and dy == 0:
                continue

            speed = asset.state.character.speed
            speed_x = speed
            speed_y = speed

            # Integer approximation for diagonal vector normalization (~0.707)
            if dx != 0 and dy != 0:
                # max(1, ...) prevents truncation paralysis for slow entities (speed < 2)
                diag_speed = max(1, (speed * 707) // 1000)
                speed_x = diag_speed
                speed_y = diag_speed

            # Apply X Vector offset 
            if dx > 0:
                asset.state.position.x += min(speed_x, dx)
            elif dx < 0:
                asset.state.position.x -= min(speed_x, abs(dx))

            # Apply Y Vector offset
            if dy > 0:
                asset.state.position.y += min(speed_y, dy)
            elif dy < 0:
                asset.state.position.y -= min(speed_y, abs(dy))

# ----------------------------------------------------------------------------------------

class CommerceMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta: float) -> None:
        """
        """
        pass

# ----------------------------------------------------------------------------------------

class CombatMechanics(Mechanic):
    """
    """

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

# ----------------------------------------------------------------------------------------

class SpeechMechanics(Mechanic):
    """
    """

    def update(self, board: Board, delta: float) -> None:
        """
        """
        pass

# ----------------------------------------------------------------------------------------

class MenuMechanics(Mechanic):
    """
    """

    def equip(self, item: str, state: SpriteState, board: Board) -> None:
        """
        """

        if item in board.equipment.weapons.keys():
            state.inventory.equipment.weapon = item
            
        elif item in board.equipment.armor.keys():
            state.inventory.equipment.armor = item
            
        elif item in board.equipment.utilities.keys():
            state.inventory.equipment.utility = item
            
        elif item in board.equipment.tools.keys():
            state.inventory.equipment.tool = item
            
        elif item in board.equipment.shields.keys():
            state.inventory.equipment.shield = item


    def update(self, board: Board, delta: float) -> None:
        """
        """
        pass