"""
@domain.model
@app.asset
@asset.state
@category.widgets

# Ontology: Source - app.models.state.assets.widgets

Widget State Models.
"""
# Standard Libraries
from typing import (
    List,
    Optional,
    Union,
    Any,
    Callable
)
from dataclasses import (
    dataclass,
    field
)

# Application Libraries
from app.static.semantics import (
    Statuses,
    Layouts,
    Fonts
)
from app.models.adapters import (
    PydanticPosition as Position,
    PydanticDimensions as Dimensions,
    PydanticMultiple as Multiple,
    Enumerated
)
from app.models.config.menus import AxisAlignment
from app.models.state.core import AssetState

# Cython Libraries
from libs.core.models import (
    Position as CorePosition,
    Dimensions as CoreDimensions,
    Multiple as CoreMultiple
)

# ------------------------------------------------------------

@dataclass(slots=True)
class WidgetState(AssetState):
    position: Position = field(default_factory=lambda: CorePosition(0, 0)) # type: ignore

# ------------------------------------------------------------

@dataclass(slots=True)
class IconState(WidgetState):
    icon_function: Callable[[], str] = field(default_factory=Callable)

    @property
    def icon(self) -> str:
        return self.icon_function()

# ------------------------------------------------------------

@dataclass(slots=True)
class TraversalState(WidgetState):
    status: Enumerated[Statuses] = Statuses.IDLE.value

# ------------------------------------------------------------

@dataclass(slots=True)
class PaneState(WidgetState):
    layout: Enumerated[Layouts] = Layouts.STACK.value
    alignment: AxisAlignment = field(default_factory=AxisAlignment)
    justification: AxisAlignment = field(default_factory=AxisAlignment)
    gap: int = 0
    margins: int = 0
    multiple: Multiple = field(default_factory=lambda: CoreMultiple(0, 0)) # type: ignore
    span: Dimensions = field(default_factory=lambda: CoreDimensions(0, 0)) # type: ignore
    content_function: Optional[Callable[[], Union[str, List[str]]]] = None
    pageindex: int = 0
    pagesize: int = 1
    font: Enumerated[Fonts] = Fonts.DIALOGUE.value
    canvas: Any = None

    @property
    def content(self) -> Union[str, List[str]]:
        if self.content_function is None:
            return ""
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
            if 0 <= self.pageindex < len(content):
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

# ------------------------------------------------------------

@dataclass(slots=True)
class MeterState(WidgetState):
    reading_function: Callable[[], Union[int, float]] = field(default_factory=Callable)
    unit_function: Callable[[], Union[int, float]] = field(default_factory=Callable)

    @property
    def reading(self) -> Union[int, float]:
        return self.reading_function()

    @property
    def unit(self) -> Union[int, float]:
        return self.unit_function()

# ------------------------------------------------------------

@dataclass(slots=True)
class CollectionState(PaneState):
    """
    ## CollectionState

    Composite state container for collection-bound macro panes (Gizmos).
    Centralizes windowing offsets, capacity limits, and item retrieval
    for delegated aperture slots.
    """
    collection_function: Callable[[], List[str]] = field(default=lambda: [])
    capacity: int = 4
    columns: int = 4
    offset: int = 0

    @property
    def collection(self) -> List[str]:
        """Evaluates the live collection closure."""
        return self.collection_function()

    def get_item(self, slot_index: int) -> str:
        """
        Retrieves the item string identifier at the windowed collection index.
        Returns an empty string for vacant slots to suppress texture rendering.
        """
        k = self.offset + slot_index
        items = self.collection
        if 0 <= k < len(items):
            return items[k]
        return ""

    def is_occupied(self, slot_index: int) -> bool:
        """Determines whether a physical aperture index holds an active entity."""
        return 0 <= (self.offset + slot_index) < len(self.collection)

    def scrollup(self) -> None:
        """Decrements offset by column count, clamped to the lower bound (0)."""
        if self.offset > 0:
            self.offset = max(0, self.offset - self.columns)

    def scrolldown(self) -> None:
        """Advances offset by column count if additional elements exist beyond capacity."""
        if self.offset + self.capacity < len(self.collection):
            self.offset += self.columns