# Task: update(dump template)

The dump template is used to dump game state at the end of a CLI session through the command,

```bash
python main.py ---dump-state start world-01
```

Assets are dynamic game entites. Widgets are Menu components. 

**Guidelines**

- Update the template to match the latest models.
- Ensure all whitespace in the Jinja2 template is properly handled.
- Enumerate all Asset, Widget and Menu fields. 
- Ensure Optional fields are handled appriopriately.
- Ensure there are new lines between the end of sections and the next heading.
- Ensure all attribute appear as nested markdown lists ,"-".

## Latest Models

### Asset State

```python
"""
# Ontology: app.models.state.core

Python data models for typing Asset state attributes.
"""
# Standard Libraries
from typing import (
    Optional, 
    Union, 
    List
)
from dataclasses import (
    dataclass,
    field
)

# Application Libraries
from app.config.enums import (
    Actions, 
    Directions,
)


# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------- CORE ASSET STATES

class NoState:
    pass

@dataclass(slots=True)
class AssetState:
    id: str
    name: Optional[str] = None
    layer: Optional[str] = None
    depth: int = 0
    height: Optional[Union[int, str]] = None

@dataclass(slots=True)
class AnimationState:
    action: str = Actions.WALK.value
    direction: str = Directions.DOWN.value
    frame: int = 0
    tick: int = 1

@dataclass(slots=True)
class PlotState:
    current: str
    previous: List[str] = field(default_factory=list)

"""
# Ontology: app.models.state.object

Python data models for typing Object state attributes.
"""
# Standard Libraries
from typing import ( 
    List,
    Optional
)
from dataclasses import dataclass, field

# Application Libraries
from app.models.adapters import (
    PydanticPosition as Position, 
    PydanticMultiple as Multiple, 
    PydanticVelocity as Velocity,
)
from app.models.state.core import (
    AnimationState,
    AssetState
)

# Cython Libraries
from libs.core.models import Velocity as CoreVelocity

# ---------------------------------------------------------------------------------------
# --------------------------------------------------------------------- GAME ASSET STATES

@dataclass(slots=True)
class MultiplierState(AssetState):
    position: Optional[Position] = None # type: ignore
    multiple: Optional[Multiple] = None # type: ignore

@dataclass(slots=True)
class PositionalState(AssetState):
    position: Optional[Position] = None # type: ignore
    velocity: Optional[Velocity] = field(default_factory=lambda: CoreVelocity(0.0, 0.0)) # type: ignore

@dataclass(slots=True)
class PropertyState(AssetState):
    owner: Optional[str] = None
    position: Optional[Position] = None # type: ignore

@dataclass(slots=True)
class DialogueState:
    persona: str
    lexicon: str
    position: Optional[Position] = None # type: ignore

@dataclass(slots=True)
class MotorState(AssetState):
    position: Optional[Position] = None # type: ignore
    initial: Optional[Position] = None # type: ignore
    direction: str = "down"
    speed: int = 10
    velocity: Optional[Velocity] = field(default_factory=lambda: CoreVelocity(0.0, 0.0)) # type: ignore

@dataclass(slots=True)
class AnimatorState(AssetState):
    position: Optional[Position] = None # type: ignore
    animation: AnimationState = field(default_factory=AnimationState)

@dataclass(slots=True)
class ContainerState(AssetState):
    content: Optional[List[str]] = field(default_factory=list)
    position: Optional[Position] = None # type: ignore
    switch: Optional[bool] = False
    animation: AnimationState = field(default_factory=AnimationState)

@dataclass(slots=True)
class DoorState(AssetState):
    position: Optional[Position] = None # type: ignore
    out: Optional[Position] = None # type: ignore
    outlayer: Optional[str] = None

@dataclass(slots=True)
class SwitchState(AssetState):
    link: Optional[str] = None
    position: Optional[Position] = None # type: ignore
    switch: Optional[bool] = False
    animation: AnimationState = field(default_factory=AnimationState)

@dataclass(slots=True)
class DialogueState(AssetState):
    position: Optional[Position] = None # type: ignore
    persona: Optional[str] = None
    lexicon: Optional[str] = None

@dataclass(slots=True)
class AttachmentState(AssetState):
    icon: Optional[str] = None
    ttl: Optional[int] = 120
    offset: Optional[Position] = None # type: ignore

"""
# Ontology: app.models.state.sprites

Python data models for typing Sprite state attributes.
"""
# Standard Libraries
from typing import (
    Dict, 
    List,
    Optional
)
from dataclasses import dataclass, field

# Application Libraries
from app.config.enums import (
    Intentions, 
    Relationships,
)
from app.models.adapters import (
    PydanticPosition as Position, 
    PydanticVelocity as Velocity,
)
from app.models.state.core import (
    AnimationState,
    AssetState
)
from app.models.state.objects import AttachmentState

# Cython Libraries
from libs.core.models import (
    Velocity as CoreVelocity, 
    Position as CorePosition
)

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------- SPRITE STATE FIELDS

@dataclass(slots=True)
class Character:
    strength: int = 10
    defense: int = 10
    speed: int = 10
    impulse: int = 10

@dataclass(slots=True)
class Equipment:
    armor: Optional[str] = None
    weapon: Optional[str] = None
    tool: Optional[str] = None
    utility: Optional[str] = None
    shield: Optional[str] = None

@dataclass(slots=True)
class Meter:
    current: int = 100
    maximum: int = 100

@dataclass(slots=True)
class Meters:
    health: Meter = field(default_factory=Meter)
    magic: Meter = field(default_factory=Meter)

@dataclass(slots=True)
class Psyche:
    persona: Optional[str] = None
    motivation: Optional[str] = None
    expression: Optional[AttachmentState] = None
    dialogue: Optional[str] = None

@dataclass(slots=True)
class Goal:
    name: Optional[str] = None
    category: Optional[str] = None
    position: Optional[Position] = field(default_factory=lambda: CorePosition(0,0)) # type: ignore

@dataclass(slots=True)
class Inventory:
    loot: Optional[Dict[str, int]] = field(default_factory=dict)
    equipment: Optional[Equipment] = field(default_factory=Equipment)
    wallet: int = 0

@dataclass(slots=True)
class Memory:
    goals: Optional[Dict[str, Goal]] = field(default_factory=dict)
    rumors: Optional[List[str]] = None
    prices: Optional[Dict[str, float]] = None
    relationships: Optional[Dict[str, Relationships]] = None
    property: Optional[Dict[str, Position]] = None # type: ignore
    sprites: Optional[Dict[str, Position]] = None # type: ignore

    def __post_init__(self) -> None:
        if self.goals is None:
            self.goals = {}
        if self.sprites is None:
            self.sprites = {}
        if self.relationships is None:
            self.relationships = {}
        if self.property is None:
            self.property = {}
        if self.rumors is None:
            self.rumors = []
            
@dataclass(slots=True)
class RadialParameters:
    radius: int

@dataclass(slots=True)
class FearParameters(RadialParameters):
    limit: float
    enemy: int

@dataclass(slots=True)
class MutatorTriggers:
    animated: bool = False
    struck: bool = False
    frightened: bool = False
    dead: bool = False
    vision: bool = False

@dataclass(slots=True)
class MutatorParameters:
    fear: FearParameters
    vision: RadialParameters
    action: RadialParameters

@dataclass(slots=True)
class Mutators:
    triggers: MutatorTriggers = field(default_factory=MutatorTriggers)
    parameters: Optional[MutatorParameters] = None

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------------- SPRITE STATES

@dataclass(slots=True)
class SpriteState(AssetState):
    intention: Optional[Intentions] = None
    goal: Optional[Goal] = field(default_factory=Goal)
    position: Optional[Position] = field(default_factory=lambda: CorePosition(0,0)) # type: ignore
    character: Optional[Character] = field(default_factory=Character)
    inventory: Optional[Inventory] = field(default_factory=Inventory)
    meters: Optional[Meters] = field(default_factory=Meters)
    mutators: Optional[Mutators] = field(default_factory=Mutators)
    memory: Optional[Memory] = field(default_factory=Memory)
    psyche: Optional[Psyche] = field(default_factory=Psyche)
    velocity: Optional[Velocity] = field(default_factory=lambda: CoreVelocity(0.0, 0.0)) # type: ignore
    animation: AnimationState = field(default_factory=AnimationState)

@dataclass(slots=True)
class PlayerState(AssetState):
    position: Optional[Position] = field(default_factory=lambda: CorePosition(0,0)) # type: ignore
    character: Optional[Character] = field(default_factory=Character)
    inventory: Optional[Inventory] = field(default_factory=Inventory)
    meters: Optional[Meters] = field(default_factory=Meters)
    mutators: Mutators = field(default_factory=Mutators)   
    goal: Optional[Goal] = field(default_factory=Goal)
    intention: Optional[Intentions] = Intentions.IDLE.value
    velocity: Optional[Velocity] = field(default_factory=lambda: CoreVelocity(0.0, 0.0)) # type: ignore
    animation: AnimationState = field(default_factory=AnimationState)
```

### Widget State

```python
"""
# Ontology: app.models.state.widget

Python data models for typing Widget state attributes.
"""
# Standard Libraries
from typing import (
    List,
    Optional, 
    Union, 
    Any, 
    Callable
)
from dataclasses import dataclass, field

# Application Libraries
from app.config.enums import (
    Statuses,
    Layouts,
    Alignments
)
from app.models.adapters import (
    PydanticPosition as Position, 
)
from app.models.state.core import (
    AssetState,
    AnimationState
)

# Cython Libraries
from libs.core.models import (
    Position as CorePosition
)
# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------------- WIDGET STATES
@dataclass(slots=True)
class IconState(AssetState):
    position: Position = field(default_factory=lambda: CorePosition(0,0)) # type: ignore
    icon_function: Callable[[], str] = field(default_factory=Callable)
    
    @property
    def icon(self) -> str:
        return self.icon_function()

@dataclass(slots=True)
class TraversalState(AssetState):
    position: Position = field(default_factory=lambda: CorePosition(0,0)) # type: ignore
    status: Statuses = Statuses.IDLE.value
    animation: AnimationState = field(default_factory=AnimationState)
    
@dataclass(slots=True)
class PaneState:
    position: Position= field(default_factory=lambda: CorePosition(0,0)) # type: ignore
    layout: Layouts = Layouts.STACK.value
    alignment: Alignments = Alignments.CENTER.value
    gap: Optional[int] = 0
    margins: Optional[int] = 0

@dataclass(slots=True)
class MeterState(AssetState):
    position: Position = field(default_factory=lambda: CorePosition(0,0)) # type: ignore
    reading_function: Callable[[], Union[int, float]] = field(default_factory=Callable)
    unit_function: Callable[[], Union[int, float]] = field(default_factory=Callable)
    animation: AnimationState = field(default_factory=AnimationState)

    @property
    def reading(self) -> Union[int, float]:
        return self.reading_function()

    @property
    def unit(self) -> Union[int, float]:
        return self.unit_function()
    
@dataclass(slots=True)
class DisplayState(AssetState):
    position: Position = field(default_factory=lambda: CorePosition(0,0)) # type: ignore
    content_function: Callable[[], Union[str, List[str]]] = field(default_factory=Callable)
    pageindex: int = 0
    pagesize: int = 1
    canvas: Any = None

    @property
    def content(self) -> Union[str, List[str]]:
        return self.content_function()

    @property
    def _pagecount(self) -> int:
        content = self.content
        if not content:
            return 0
        if isinstance(content, list):
            return len(content)
        return 1

    def current(self) -> str:
        content = self.content
        if not content:
            return ""
        if isinstance(content, list):
            if self.pageindex < len(content):
                return content[self.pageindex]
            return ""
        return content

    def more(self) -> bool: 
        return self.pageindex < (self._pagecount - 1)

    def less(self) -> bool:
        return self.pageindex > 0

    def scrollup(self) -> None: 
        if self.less():
            self.pageindex -= 1

    def scrolldown(self) -> None:
        if self.more():
            self.pageindex += 1
```

### Menu State


```python
"""
# Ontology: app.models.config.menus

Models for typing the configuration attributes of Menus.
"""
# Standard Libraries
from typing import (
    List, 
    Optional, 
    Union
)
from dataclasses import dataclass

# Application Libraries
from app.config.enums import (
    Statuses,
    Layouts,
    Alignments,
)
from app.game.menus.core import Binding
from app.models.adapters import (
    PydanticScreenPosition as ScreenPosition
)
from app.models.config.core import Configuration

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------- MENU CONFIGURATION

@dataclass(slots=True, frozen=True)
class MenuWidget:
    instance: str
    id: str
    name: str
    bind: Optional[Binding] = None
    status: Optional[Statuses] = Statuses.IDLE

@dataclass(slots=True, frozen=True)
class MenuPane:
    id: str 
    name: str
    layout: Layouts
    alignment: Alignments
    gap: int
    children: List[Union['MenuPane', MenuWidget]]
    margins: Optional[int] = 0
    position: Optional[ScreenPosition] = None # type: ignore

@dataclass(slots=True, frozen=True)
class MenuConfiguration(Configuration):
    controller: str
    roots: List[MenuPane]

@dataclass(slots=True)
class Binding:
    selection: Optional[str] = None
    selector: Optional[str] = None
    state: Optional[str] = None
```

## Previous Dump Template

```jinja2
# Ontology State Dump

**Board:** {{ board_key }}
**Timestamp:** {{ timestamp }}

---

{% for asset in assets %}
## {{ asset.name }} 

**Taxonomy:** 
  - Category: `{{ asset.category }}` 
  - Instance: `{{ asset.instance }}`
  - ID: `{{ asset.id }}`
**Layer:** {{ asset.state.layer }}
{% if asset.state.position -%}
- **Position:** ({{ asset.state.position.x }}, {{ asset.state.position.y }})
{% endif -%}
{% if asset.state.multiple -%}
- **Multiple:** nx: {{ asset.state.multiple.nx }}, ny: {{ asset.state.multiple.ny }}
{% endif -%}
{% if asset.state.animation -%}
- **Animation:** 
  - Action: `{{ asset.state.animation.action }}`
  - Direction: `{{ asset.state.animation.direction }}`
  - Frame: `{{ asset.state.animation.frame }}`
{% endif -%}
{% if asset.state.switch is defined -%}
- **Switch:** {{ asset.state.switch }}
{% endif -%}
{% if asset.state.content is defined -%}
- **Content:** {{ asset.state.content }}
{% endif -%}
{% if asset.state.link -%}
- **Link:** {{ asset.state.link }}
{% endif -%}
{% if asset.state.outlayer -%}
- **Door Out:** Layer: {{ asset.state.outlayer }}, Position: ({{ asset.state.out.x }}, {{ asset.state.out.y }})
{% endif -%}
{% if asset.state.owner -%}
- **Owner:** {{ asset.state.owner }}
{% endif -%}
{% if asset.state.character -%}
- **Character:** STR: {{ asset.state.character.strength }}, DEF: {{ asset.state.character.defense }}, SPD: {{ asset.state.character.speed }}
{% endif -%}
{% if asset.state.psyche %}
- **Psyche**:
  - Dialogue: {{ asset.state.psyche.dialogue }}
  - Expression: {{ asset.state.psyche.expression }}
{% endif %}
{% if asset.state.meters -%}
- **Meters:**
  - Health: {{ asset.state.meters.health.current }} / {{ asset.state.meters.health.maximum }}
  - Magic: {{ asset.state.meters.magic.current }} / {{ asset.state.meters.magic.maximum }}
{% endif -%}
{% if asset.state.inventory -%}
- **Inventory:**
  - Wallet: {{ asset.state.inventory.wallet }}
  - Equipment: 
    - Armor: `{{ asset.state.inventory.equipment.armor }}` 
    - Weapon: `{{ asset.state.inventory.equipment.weapon }}`
    - Tool: `{{ asset.state.inventory.equipment.tool }}`
    - Utility: `{{ asset.state.inventory.equipment.utility }}`
    - Shield: `{{ asset.state.inventory.equipment.shield }}`
{% endif -%}
{% if asset.state.goal -%}
- **Goal:** 
  - Name: `{{ asset.state.goal.name }}`
  - Category: `{{ asset.state.goal.category }}`
  - Position: ({{ asset.state.goal.position.x }}, {{ asset.state.goal.position.y }})
{% endif -%}
{% if asset.state.memory -%}
- **Memory:** 
  - Goals:
  {% for goal in asset.state.memory.goals.values() %}
    - Name: `{{ goal.name }}`
    - Category: `{{ goal.category }}`
    - Position: `({{ goal.position.x }}, {{ goal.position.y }})` 
  {% endfor%}
  - Sprites:
  {% for name, position in asset.state.memory.sprites.items() %}
    - Name: `{{ name }}`
    - Position: `({{ position.x }}, {{ position.y }})`
  {% endfor %}
  - Relationships: `{{ asset.state.memory.relationships }}`
{% endif -%}
{% if asset.state.intention -%}
- **Intention:** `{{ asset.state.intention }}`
{% endif -%}
{%- endfor -%}
{%- for section_name, menu_list in [('Menus', menus), ('Overlays', overlays)] %}
{%- if menu_list -%}
---

# {{ section_name }}

{% for menu in menu_list %}
## {{ section_name[:-1] }}: {{ menu.id }}

**Focus:** `{{ menu.focus }}`
**Context:** {{ menu.context }}

### Widgets
{% for w_key, widget in menu.widgets.items() %}
#### {{ widget.name }} (`{{ widget.id }}`)

**Taxonomy:** 
  - Category: `{{ widget.category }}` 
  - Instance: `{{ widget.instance }}`
  - ID: `{{ widget.id }}`
**Component Classes:**
  - Frame: `{{ widget.frame.__class__.__name__ }}`
  - Animation: `{{ widget.animation.__class__.__name__ }}`
**Calculated Values:**
  - Computed Keys: `{{ widget.frame.keys(widget.id, widget.state) }}`
**Properties**:
  - Dimensions: w: {{ widget.dimensions.w }}, l: {{ widget.dimensions.l }}
{% if widget.binding -%}
**Binding:**
  - Selection: `{{ widget.binding.selection }}`
  - Selector: `{{ widget.binding.selector }}`
  - State: `{{ widget.binding.state }}`
{% endif -%}
**State:**
{% if widget.state.position -%}
  - Position: ({{ widget.state.position.x }}, {{ widget.state.position.y }})
{% endif -%}
{% if widget.state.status is defined -%}
  - Status: `{{ widget.state.status }}`
{% endif -%}
{% if widget.state.content is defined -%}
  - Content: {{ widget.state.content }}
{% endif -%}
{% if widget.state.reading is defined -%}
  - Reading: {{ widget.state.reading }} / {{ widget.state.unit }}
{% endif -%}
{% endfor %}
{% endfor %}
{% endif %}
{% endfor %}
```