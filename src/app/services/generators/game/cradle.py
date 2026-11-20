"""
@domain.system
@app.service
@workflow.injection
@workflow.crafting
@workflow.combat

# Ontology: Source - app.services.generators.game.cradle

Package for ingame Asset instantiation.
"""
from __future__ import annotations

# Standard Libraries
import math
from typing import (
    TYPE_CHECKING,
    List,
    Optional,
    Union,
)
import logging 
import uuid

# Application Libraries
import app.static.settings as settings
from app.assets.base import Asset
from app.static.semantics import (
    AssetInstances, 
    AssetCategories,
    Orientations,
    Directions,
    # ---------
    Ceramics,
    Chromatics,
    Geologics,
    Metallics,
    Organics,
    # ---------
    Buildings,
    Corridors,
    Columns,
    Enclosures,
    Inclines,
)
from app.game.logic.relations import MaterialIndex
from app.services.factories.assets import AssetFactory
from app.models.config import RecipeConfiguration
from app.models.groups import SpawnableGroup
from app.models.state import (
    AnimationState,
    CraftState,
    MotorState, 
    PropertyState,
    AttachmentState,
    EffectState,
    HazardState,
    CollectableState,
    ShorelineState,
    Damage,
    Lot
)

if TYPE_CHECKING:
    from app.services.generators.game.decomposer import Decomposer

from libs.core.models import (
    Hitbox,
    Position, 
    Velocity,
    Multiple
)

logger = logging.getLogger(__name__)

SPAWN = "spawn"

_DIRECTION_ANGLES = {
    Directions.RIGHT: 0.0,
    Directions.DOWN: 90.0,
    Directions.LEFT: 180.0,
    Directions.UP: 270.0,
}

class Cradle:
    """
    ## Cradle
    Responsible for creating Asset Instances on the fly during the engine loop.
    """
    recipes: RecipeConfiguration
    spawnables: SpawnableGroup
    decomposer: Decomposer
    materials: MaterialIndex

    def __init__(self, 
        spawnables: SpawnableGroup, 
        recipes: RecipeConfiguration, 
        materials: MaterialIndex,
        decomposer: Decomposer
    ):
        self.spawnables = spawnables
        self.recipes = recipes
        self.materials = materials
        self.decomposer = decomposer


    @staticmethod
    def name() -> str:
        return settings.SEPARATOR.join([ SPAWN, uuid.uuid4().hex[:8] ])

    
    def spawn_expression(self, 
        id: str, 
        icon: str, 
        target: Asset
    ) -> AttachmentState:
        properties = self.spawnables.expressions.get(id)
        
        # Calculate top-right anchor using properties and target dimensions
        if properties and target.dimensions:
            ox = target.dimensions.w - 2*properties.dimensions.w
            # TODO: parameterize or shift to properties
            oy = -0.9*properties.dimensions.l
        else:
            ox, oy = 0, 0
            
        return AttachmentState(
            id=id,
            layer=target.state.layer,
            icon=icon, 
            offset=Position(x=ox, y=oy),
            ttl=settings.EXPRESSION_TTL
        )


    def spawn_projectile(
        self,
        id: str,
        position: Position,                 # type: ignore
        layer: str,
        direction: Optional[str] = None,
        target: Optional[Position] = None,  # type: ignore
        speed: int = 200,
        elevation: int = 0,
        owner: Optional[str] = None,
    ) -> Asset:
        """
        Instantiates a Projectile centered on `position` with quantized launch angle,
        drift-free cardinal velocity components, distinct initial/position coordinates,
        and ownership metadata.
        """
        properties = self.spawnables.projectiles.get(id)
        if not properties:
            raise ValueError(f"Unknown projectile asset ID: '{id}'")

        # Center projectile frame top-left origin on the release coordinate
        origin_x = position.x - (properties.dimensions.w // 2)
        origin_y = position.y - (properties.dimensions.l // 2)
        spawn_pos = Position(origin_x, origin_y)
        initial_pos = Position(origin_x, origin_y)

        # Derive continuous launch angle in screen coordinates (+x right, +y down)
        if target is not None and (target.x != position.x or target.y != position.y):
            dx = target.x - position.x
            dy = target.y - position.y
            raw_angle = math.degrees(math.atan2(dy, dx)) % 360.0
        elif direction in _DIRECTION_ANGLES:
            raw_angle = _DIRECTION_ANGLES[direction]
        else:
            raw_angle = 0.0

        # Quantize angle onto discrete texture strip rotation step
        step = properties.rotation if properties.rotation is not None else 90
        angle = (round(raw_angle / step) * step) % 360

        # Clamp cardinal trig drift to exact axis vectors
        if angle == 0:
            vx, vy = float(speed), 0.0
        elif angle == 90:
            vx, vy = 0.0, float(speed)
        elif angle == 180:
            vx, vy = -float(speed), 0.0
        elif angle == 270:
            vx, vy = 0.0, -float(speed)
        else:
            rad = math.radians(angle)
            vx = speed * math.cos(rad)
            vy = speed * math.sin(rad)

        state = MotorState(
            id=id,
            name=self.name(),
            layer=layer,
            elevation=elevation,
            position=spawn_pos,
            initial=initial_pos,
            velocity=Velocity(vx, vy),
            angle=angle,
            speed=speed,
            owner=owner,
        )

        return AssetFactory.asset(
            category=AssetCategories.CURSORS,
            instance=AssetInstances.PROJECTILES,
            properties=properties,
            state=state,
            recipe=self.recipes.cursors.projectiles,
            substrate=self.materials.substrate(AssetInstances.PROJECTILES)
        )


    def spawn_collectable(self, 
        id: str, 
        layer: str, 
        position: Position,
        lot: Lot
    ) -> Asset:
        state = CollectableState(
            id=id,
            name=self.name(),
            layer=layer,
            position=position,
            lot=lot
        )
        return AssetFactory.asset(
            category=AssetCategories.EFFECTS,
            instance=AssetInstances.COLLECTABLES,
            properties=self.spawnables.collectables.get(id),
            state=state,
            recipe=self.recipes.effects.collectables,
            substrate=self.materials.substrate(AssetInstances.COLLECTABLES)
        )


    def spawn_hazard(self, 
        id: str, 
        layer: str, 
        position: Position,
        damage: Damage
    ) -> Asset:
        state = HazardState(
            id=id,
            name=self.name(),
            layer=layer,
            position=position,
            damage=damage
        )
        return AssetFactory.asset(
            category=AssetCategories.EFFECTS,
            instance=AssetInstances.HAZARDS,
            properties=self.spawnables.hazards.get(id),
            state=state,
            recipe=self.recipes.effects.hazards,
            substrate=self.materials.substrate(AssetInstances.HAZARDS)
        )


    def spawn_passive(self, id: str, layer: str, position: Position) -> Asset:
        state = EffectState(
            id=id,
            name=self.name(),
            layer=layer,
            position=position,
            animation=AnimationState()
        )
        return AssetFactory.asset(
            category=AssetCategories.EFFECTS,
            instance=AssetInstances.PASSIVE,
            properties=self.spawnables.passive.get(id),
            state=state,
            recipe=self.recipes.effects.passive,
            substrate=self.materials.substrate(AssetInstances.PASSIVE)
        )


    def spawn_shoreline(self,
        id: str,
        layer: str,
        position: Position,
        orientation: str,
        length: int,
        hitboxes: List[Hitbox],  # type: ignore
    ) -> Asset:
        properties = self.spawnables.shorelines.get(id)

        state = ShorelineState(
            id=id,
            name=self.name(),
            layer=layer,
            position=position,
            orientation=orientation,
            length=length,
            hitboxes=hitboxes
        )
        return AssetFactory.asset(
            category=AssetCategories.GEOGRAPHY,
            instance=AssetInstances.SHORELINES,
            properties=properties,
            state=state,
            recipe=self.recipes.geography.shorelines,
            substrate=self.materials.substrate(AssetInstances.SHORELINES)
        )


    def spawn_composition(self, 
        id: str, 
        position: Position,  # type: ignore,
        material: Union[Ceramics,Chromatics,Geologics,Metallics,Organics],
        blueprint: Union[Buildings,Corridors,Columns,Enclosures,Orientations,Inclines,Directions],
        layer: str, 
        owner: str
    ) -> List[Asset]:
        """
        Dynamically spawn an entire composition schema through the engine's mechanics flow.
        """
        pseudo_state = PropertyState(
            id          = id, 
            name        = self.name(), 
            layer       = layer, 
            position    = position, 
            material    = material,
            blueprint   = blueprint,
            owner       = owner
        )
        return self.decomposer.unpack(pseudo_state)


    def spawn_bridge(
        self,
        id: str,
        layer: str,
        position: Position,
        material: Union[Geologics,Metallics,Organics],
        blueprint: Orientations,
        multiple: Multiple
    ) -> List[Asset]:
        """
        Spawns and unpacks a bridge configuration via Decomposer.
        """
        bridge_state = CraftState(
            id=id,
            name=self.name(),
            layer=layer,
            position=position,
            material=material,
            blueprint=blueprint,
            multiple=multiple
        )
        return self.decomposer.multiply(
            bridge_state,
            AssetCategories.CRAFTS,
            AssetInstances.BRIDGES
        )