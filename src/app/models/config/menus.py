"""
# Ontology: app.models.config.menus

Models for typing the configuration attributes of Menus.
"""
# Standard Libraries
from typing import (
    List, 
    Optional, 
    Union,
    Dict
)
from dataclasses import dataclass

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

# ---------------------------------------------------------------------------------------
# -------------------------------------------------------------------- MENU CONFIGURATION

@dataclass(slots=True, frozen=True)
class MenuBinding:
    schema: str = None
    target: Union[str, Dict[str, str]] = None


@dataclass(slots=True, frozen=True)
class MenuWidget:
    instance: str
    id: str
    name: str
    bind: Optional[MenuBinding] = None
    status: Optional[Statuses] = Statuses.IDLE


@dataclass(slots=True, frozen=True)
class MenuGizmo:
    """
    Declarative macro node within a Menu configuration tree.
    Bridges static UI layouts with dynamic collection data.
    """
    id: str
    name: str
    bind: MenuBinding
    capacity: int
    columns: int
    gap: int = 5
    pane: str = "transparent-slot"
    button: str = "slot"

    def __post_init__(self):
        if self.capacity <= 0:
            raise ValueError(f"MenuGizmo capacity must be greater than 0, got {self.capacity}")
        if self.columns <= 0:
            raise ValueError(f"MenuGizmo columns must be greater than 0, got {self.columns}")
        if not self.pane:
            raise ValueError("MenuGizmo pane identifier cannot be empty")
        if not self.button:
            raise ValueError("MenuGizmo button identifier cannot be empty")

    @property
    def pane_id(self) -> str:
        return self.pane

    @property
    def button_id(self) -> str:
        return self.button


@dataclass(slots=True, frozen=True)
class MenuPane:
    id: str 
    name: str
    layout: Layouts
    alignment: Alignments
    children: List[Union['MenuPane', MenuWidget, MenuGizmo]]
    gap: Optional[int] = 0
    margins: Optional[int] = 0
    position: Optional[ScreenPosition] = None  # type: ignore
    font: Optional[str] = None
    dimensions: Optional[Dimensions] = None # type: ignore

@dataclass(slots=True, frozen=True)
class MenuConfiguration(Configuration):
    controller: str
    roots: List[MenuPane]