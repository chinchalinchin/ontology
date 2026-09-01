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
    AnimationState
)

# ---------------------------------------------------------------------------------------
# ------------------------------------------------------------------------- WIDGET STATES

@dataclass(slots=True)
class IconState:
    position: Position # type: ignore
    icon: str

@dataclass(slots=True)
class TraversalState:
    position: Position # type: ignore
    status: Statuses
    animation: AnimationState = field(default_factory=AnimationState)
    
@dataclass(slots=True)
class PaneState:
    position: Position # type: ignore
    layout: Layouts
    alignment: Alignments
    gap: int
    margins: Optional[int] = 0

@dataclass(slots=True)
class MeterState:
    position: Position # type: ignore
    reading_function: Callable[[], Union[int, float]]
    unit_function: Callable[[], Union[int, float]]
    animation: AnimationState = field(default_factory=AnimationState)

    @property
    def reading(self) -> Union[int, float]:
        return self.reading_function()

    @property
    def unit(self) -> Union[int, float]:
        return self.unit_function()
    
@dataclass(slots=True)
class DisplayState:
    position: Position # type: ignore
    content: Union[str, List[str]]
    pageindex: int
    pagesize: int = 1
    canvas: Any = None

    @property
    def _pagecount(self) -> int:
        if not self.content:
            return 0
        if isinstance(self.content, list):
            return len(self.content)
        return 1

    def current(self) -> str:
        if not self.content:
            return ""
        if isinstance(self.content, list):
            if self.pageindex < len(self.content):
                return self.content[self.pageindex]
            return ""
        return self.content

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