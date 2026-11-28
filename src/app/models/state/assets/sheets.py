"""
@domain.model
@app.asset
@asset.state
@category.sheets

# Ontology: Source - app.models.state.assets.sheets

Sheet State Models.
"""
# Standard Libraries
from typing import (
    Dict,
    List,
    Optional
)
from dataclasses import dataclass, field

# Application Libraries
from app.static.semantics import (
    Goals,
    Intentions,
    Motivations,
    Relationships,
    ItemPalette,
    ArmorPalette,
    ShieldPalette,
    ToolPalette,
    UtilityPalette,
    WeaponPalette,
    MaterialPalette,
    CropPalette
)
from app.models.adapters import (
    PydanticPosition as Position,
    PydanticVelocity as Velocity,
    Enumerated
)
from app.models.state.core import (
    AnimationState,
    AssetState
)
from app.models.state.assets.cursors import AttachmentState

# Cython Libraries
from libs.core.models import (
    Velocity as CoreVelocity,
    Position as CorePosition
)

# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class Character:
    strength: int = 10
    defense: int = 10
    speed: int = 10
    impulse: int = 10

# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class Meter:
    current: int = 100
    maximum: int = 100

@dataclass(slots=True)
class Meters:
    health: Meter = field(default_factory=Meter)
    magic: Meter = field(default_factory=Meter)

# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class Equipment:
    armor: Optional[Enumerated[ArmorPalette]] = None
    weapon: Optional[Enumerated[WeaponPalette]] = None
    tool: Optional[Enumerated[ToolPalette]] = None
    utility: Optional[Enumerated[UtilityPalette]] = None
    shield: Optional[Enumerated[ShieldPalette]] = None

@dataclass(slots=True)
class Grip:
    left: Optional[Enumerated[ItemPalette]] = None
    right: Optional[Enumerated[ItemPalette]] = None

@dataclass(slots=True)
class Slots:
    equipment: Equipment = field(default_factory=Equipment)
    grip: Grip = field(default_factory=Grip)

@dataclass(slots=True)
class Inventory:
    # List Fields (i.e. inventory with only one instance)
    bag: List[Enumerated[UtilityPalette]] = field(default_factory=list)
    belt: List[Enumerated[ToolPalette]] = field(default_factory=list)
    sheathe: List[Enumerated[WeaponPalette]] = field(default_factory=list)
    # Dict Fields (i.e. inventory that can be accumulated)
    pouch: Dict[
        Enumerated[ItemPalette],
        int
    ] = field(default_factory=dict)
    pack: Dict[
        Enumerated[MaterialPalette],
        int
    ] = field(default_factory=dict)
    sack: Dict[
        Enumerated[CropPalette],
        int
    ] = field(default_factory=dict)

# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class Psyche:
    persona: Optional[str] = None
    motivation: Optional[Enumerated[Motivations]] = None
    expression: Optional[AttachmentState] = None
    dialogue: Optional[str] = None

@dataclass(slots=True)
class Goal:
    name: Optional[str] = None
    category: Optional[Enumerated[Goals]] = None
    layer: Optional[str] = None
    position: Position = field(default_factory=lambda: CorePosition(0, 0))  # type: ignore
    dormant: bool = False

@dataclass(slots=True)
class Memory:
    goals: Dict[str, Goal] = field(default_factory=dict)
    rumors: List[str] = field(default_factory=list)
    prices: Dict[str, float] = field(default_factory=dict)
    relationships: Dict[str, Enumerated[Relationships]] = field(default_factory=dict)
    property: Dict[str, Position] = field(default_factory=dict)  # type: ignore
    sprites: Dict[str, Position] = field(default_factory=dict)  # type: ignore
    doors: Dict[str, Dict[str, str]] = field(default_factory=dict)
    stack: List[Goal] = field(default_factory=list)

@dataclass(slots=True)
class Trajectory:
    target: Optional[Position] = None  # type: ignore
    vertices: List[Position] = field(default_factory=list)  # type: ignore
    stalled: bool = False
    cooldown: int = 0

# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class SheetState(AssetState):
    """Base animated Sheet state (Pixies)."""
    position: Position = field(default_factory=lambda: CorePosition(0, 0))  # type: ignore
    velocity: Velocity = field(default_factory=lambda: CoreVelocity(0.0, 0.0))  # type: ignore
    animation: AnimationState = field(default_factory=AnimationState)

# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class CharacterState(SheetState):
    """Intentional Sheet state with equipment, inventory, meters, and Goal (Players)."""
    intention: Enumerated[Intentions] = Intentions.IDLE
    character: Character = field(default_factory=Character)
    slots: Slots = field(default_factory=Slots)
    inventory: Inventory = field(default_factory=Inventory)
    meters: Meters = field(default_factory=Meters)
    goal: Optional[Goal] = None

# ---------------------------------------------------------------------------------------

@dataclass(slots=True)
class SpriteState(CharacterState):
    """Autonomous Character state with Memory, Psyche, and Trajectory (Sprites)."""
    memory: Memory = field(default_factory=Memory)
    psyche: Psyche = field(default_factory=Psyche)
    trajectory: Trajectory = field(default_factory=Trajectory)