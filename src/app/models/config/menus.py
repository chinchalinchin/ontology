"""
@domain.model
@app.config
@app.menu

# Ontology: Source - app.models.config.menus

Models for typing the configuration attributes of Menus.
"""
from __future__ import annotations

# Standard Libraries
from typing import (
    List, 
    Optional, 
    Union, 
)
from dataclasses import (
    dataclass, 
    field
)

# Application Libraries
from app.static.semantics import (
    Statuses,
    Layouts,
    Bindings,
    Controllers,
    Selections,
    Fonts,
    Widgets
)
from app.models.adapters import (
    PydanticScale as Scale,
    PydanticDimensions as Dimensions,
    Enumerated
)
from app.models.core import AxisAlignment
from app.models.config import Configuration
from app.models.adapters import Enumerated

# Cython Libraries
from libs.core.models import Scale as CoreScale
# ---------------------------------------------------------

@dataclass(slots=True, frozen=True)
class LibraryTarget:
    plot: str
    persona: str
    lexicon: str


@dataclass(slots=True, frozen=True)
class MeterTarget:
    meter: str


@dataclass(slots=True, frozen=True)
class IconTarget:
    icon: str


@dataclass(slots=True, frozen=True)
class TextTarget:
    content: str


@dataclass(slots=True, frozen=True)
class CollectionTarget:
    source: str
    capacity: int = 8
    columns: int = 4


@dataclass(slots=True, frozen=True)
class ApertureTarget:
    selector: str
    index: int


@dataclass(slots=True, frozen=True)
class SelectTarget:
    selection: Enumerated[Selections] = Statuses.IDLE.value
    selector: Optional[str] = None
    index: Optional[int] = None


# ---------------------------------------------------------

BindingTarget = Union[
    LibraryTarget,
    MeterTarget,
    IconTarget,
    TextTarget,
    CollectionTarget,
    # NOTE: SelectTarget must come before ApertureTarget
    #           or else Pydantic validators will enforce
    #           wrong typing.
    SelectTarget,
    ApertureTarget,
]

# ---------------------------------------------------------

@dataclass(slots=True, frozen=True)
class MenuBinding:
    """
    Associates UI controls or panes with runtime context paths or commands.
    """
    schema: Enumerated[Bindings]
    target: BindingTarget

# ---------------------------------------------------------


@dataclass(slots=True, frozen=True)
class PaneParameters:
    """
    Structural and spatial layout parameters for container panes.
    """
    layout: Enumerated[Layouts] = Layouts.STACK.value
    alignment: AxisAlignment = field(default_factory=AxisAlignment)
    justification: AxisAlignment = field(default_factory=AxisAlignment)
    gap: int = 0
    margins: int = 0
    dimensions: Scale = field(default_factory=lambda: CoreScale(1.0, 1.0)) # type: ignore
    font: Optional[Enumerated[Fonts]] = None
    children: List[MenuNode] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class GizmoParameters:
    """
    Macro expansion configuration for virtual collection gizmos.
    """
    capacity: int
    columns: int
    pane: str
    button: str
    dimensions: Scale = field(default_factory=lambda: CoreScale(1.0, 1.0)) # type: ignore
    gap: int = 5

    def __post_init__(self):
        if self.capacity <= 0:
            raise ValueError(f"GizmoParameters capacity must be greater than 0, got {self.capacity}")
        if self.columns <= 0:
            raise ValueError(f"GizmoParameters columns must be greater than 0, got {self.columns}")
        if not self.pane:
            raise ValueError("GizmoParameters pane identifier cannot be empty")
        if not self.button:
            raise ValueError("GizmoParameters button identifier cannot be empty")


@dataclass(slots=True, frozen=True)
class ButtonParameters:
    """
    State parameters for traversable interactive button widgets.
    """
    status: Enumerated[Statuses] = Statuses.IDLE.value

# ---------------------------------------------------------

@dataclass(slots=True, frozen=True)
class MenuNode:
    """
    Unified AST node representing panes, widgets, and virtual macro gizmos.
    """
    id: str
    name: str
    instance: Enumerated[Widgets]
    bind: Optional[MenuBinding] = None
    parameters: Optional[Union[PaneParameters, GizmoParameters, ButtonParameters]] = None

# ---------------------------------------------------------

@dataclass(slots=True, frozen=True)
class MenuConfiguration(Configuration):
    """
    Root menu configuration containing high-level controller and node hierarchy.
    """
    controller: Enumerated[Controllers]
    roots: List[MenuNode]