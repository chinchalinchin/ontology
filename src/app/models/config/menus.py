"""
# Ontology: app.models.config.menus

Models for typing the configuration attributes of Menus.
"""
from __future__ import annotations

# Standard Libraries
from typing import (
    List, 
    Optional, 
    Union, 
    Dict,
)
from dataclasses import dataclass, field

# Application Libraries
from app.config.enums import (
    Statuses,
    Layouts,
    Alignments
)
from app.models.adapters import (
    PydanticScreenPosition as ScreenPosition,
    PydanticDimensions as Dimensions
)
from app.models.config.core import Configuration


@dataclass(slots=True, frozen=True)
class MenuBinding:
    """
    Associates UI controls or panes with runtime context paths or commands.
    """
    schema: Optional[str] = None
    target: Optional[Union[str, Dict[str, str]]] = None


@dataclass(slots=True, frozen=True)
class PaneParameters:
    """
    Structural and spatial layout parameters for container panes.
    """
    layout: Layouts = Layouts.STACK.value
    alignment: Alignments = Alignments.START.value
    gap: int = 0
    margins: int = 0
    position: Optional[ScreenPosition] = None # type: ignore
    dimensions: Optional[Dimensions] = None # type: ignore
    font: Optional[str] = None
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
    status: Statuses = Statuses.IDLE


@dataclass(slots=True, frozen=True)
class MenuNode:
    """
    Unified AST node representing panes, widgets, and virtual macro gizmos.
    """
    id: str
    name: str
    instance: str
    bind: Optional[MenuBinding] = None
    parameters: Optional[Union[PaneParameters, GizmoParameters, ButtonParameters]] = None


@dataclass(slots=True, frozen=True)
class MenuConfiguration(Configuration):
    """
    Root menu configuration containing high-level controller and node hierarchy.
    """
    controller: str
    roots: List[MenuNode]

# NOTE: backwards compatibility is pointless when we are in the process of refactoring this exact functionality. let it fail, so we know where the bugs are.