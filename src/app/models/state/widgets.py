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