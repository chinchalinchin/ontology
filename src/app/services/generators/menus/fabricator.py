"""
# Ontology: app.services.generators.menus.fabricator

Package for constructing Gizmos.
"""
# Standard Libraries
from typing import Optional, List, Any

# Application Libraries
from app.config.enums import (
    AssetInstances,
    Layouts,
    Alignments,
    Statuses
)
from app.models.config.menus import (
    MenuGizmo,
    MenuPane,
    MenuWidget,
    MenuBinding
)
from app.models.properties import WidgetProperties
from app.game.menus.contexts import MenuContext

# Cython Libraries
from libs.core.models import Dimensions

class Fabricator:
    """
    ## Fabricator

    Macro expansion generator service that transforms declarative MenuGizmo nodes
    into concrete MenuPane and MenuWidget subtrees prior to layout resolution and ECS instantiation.
    """

    @staticmethod
    def _extract_source_path(bind: Optional[MenuBinding]) -> str:
        if not bind or not bind.target:
            return ""
        if isinstance(bind.target, str):
            return bind.target
        return bind.target.get("source", bind.target.get("collection", ""))

    @staticmethod
    def _resolve_collection_len(path: str, context: Optional[MenuContext]) -> Optional[int]:
        if not context or not path or not path.startswith("context."):
            return None
        parts = path.split(".")[1:]
        current: Any = context
        for part in parts:
            if current is None:
                return None
            if isinstance(current, dict):
                current = current.get(part)
            else:
                current = getattr(current, part, None)
        if isinstance(current, list):
            return len(current)
        return None

    @classmethod
    def expand(
        cls,
        gizmo: MenuGizmo,
        context: MenuContext,
        properties: WidgetProperties
    ) -> MenuPane:
        source_path = gizmo.bind.target["source"] \
                        if isinstance(gizmo.bind.target, dict) \
                            else gizmo.bind.target
        slot_props = properties.panes[gizmo.pane]
        slot_w = slot_props.dimensions.w
        slot_l = slot_props.dimensions.l

        capacity = gizmo.capacity
        columns = gizmo.columns
        total_rows = (capacity + columns - 1) // columns

        row_w = columns * slot_w + (columns - 1) * gizmo.gap
        row_l = slot_l
        grid_w = row_w
        grid_l = total_rows * slot_l + (total_rows - 1) * gizmo.gap

        row_panes: List[MenuPane] = []

        for row_idx in range(total_rows):
            start_slot = row_idx * columns
            end_slot = min(start_slot + columns, capacity)
            slot_panes: List[MenuPane] = []

            for slot_idx in range(start_slot, end_slot):
                button_name = f"{gizmo.name}-slot-{slot_idx}"
                icon_name = f"{gizmo.name}-icon-{slot_idx}"

                button_widget = MenuWidget(
                    instance=AssetInstances.BUTTONS.value,
                    id=gizmo.button,
                    name=button_name,
                    bind=MenuBinding(
                        schema="select",
                        target={
                            "selection": "slot",
                            "selector": icon_name,
                            "source": source_path,
                            "index": str(slot_idx)
                        }
                    ),
                    status=Statuses.IDLE
                )

                icon_widget = MenuWidget(
                    instance=AssetInstances.ICONS.value,
                    id=gizmo.id,
                    name=icon_name,
                    bind=MenuBinding(
                        schema="collection",
                        target={
                            "source": source_path,
                            "index": str(slot_idx),
                            "offset": "0"
                        }
                    ),
                    status=Statuses.IDLE
                )

                slot_container = MenuPane(
                    id=gizmo.pane,
                    name=f"{gizmo.name}-slot-{slot_idx}-pane",
                    layout=Layouts.OVERLAY,
                    alignment=Alignments.CENTER,
                    gap=0,
                    margins=0,
                    dimensions=Dimensions(w=slot_w, l=slot_l),
                    children=[button_widget, icon_widget]
                )
                slot_panes.append(slot_container)

            row_pane = MenuPane(
                id=gizmo.pane,
                name=f"{gizmo.name}-row-{row_idx}",
                layout=Layouts.DOCK,
                alignment=Alignments.START,
                gap=gizmo.gap,
                margins=0,
                dimensions=Dimensions(w=row_w, l=row_l),
                children=slot_panes
            )
            row_panes.append(row_pane)

        return MenuPane(
            id=gizmo.pane,
            name=gizmo.name,
            layout=Layouts.STACK,
            alignment=Alignments.START,
            gap=gizmo.gap,
            margins=0,
            dimensions=Dimensions(w=grid_w, l=grid_l),
            children=row_panes
        )