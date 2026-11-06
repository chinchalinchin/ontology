"""
@domain.system
@app.menu
@app.service
@menu.gizmo

# Ontology: Source - app.services.generators.menus.fabricator

Package for constructing Gizmos.
"""
# Standard Libraries
from typing import (
    List,
    Dict,
    Callable
)

# Application Libraries
from app.static.semantics import (
    AssetInstances,
    Layouts,
    Alignments,
    Statuses,
    Selections,
    Bindings
)
from app.models.config.menus import (
    MenuNode,
    PaneParameters,
    GizmoParameters,
    ButtonParameters,
    MenuBinding,
    CollectionTarget,
    SelectTarget,
    ApertureTarget
)
from app.models.properties import WidgetProperties
from app.models.menus import MenuContext

# Cython Libraries
from libs.core.models import Dimensions


class Fabricator:
    """
    Transforms declarative virtual MenuNode(instance="gizmos") into
    concrete MenuNode(instance="panes") subtrees based on binding schema.
    """

    @classmethod
    def expand(
        cls,
        node: MenuNode,
        context: MenuContext,
        properties: WidgetProperties
    ) -> MenuNode:
        if not node.bind or not node.bind.schema:
            raise ValueError(f"Gizmo '{node.name}' declared without a binding schema.")

        handlers: Dict[str, Callable[[MenuNode, MenuContext, WidgetProperties], MenuNode]] = {
            Bindings.COLLECTION.value: cls._collection,
        }

        handler = handlers.get(node.bind.schema)
        if not handler:
            raise NotImplementedError(
                f"Unsupported gizmo schema '{node.bind.schema}' for node '{node.name}'."
            )

        return handler(node, context, properties)

    @classmethod
    def _collection(
        cls,
        node: MenuNode,
        context: MenuContext,
        properties: WidgetProperties
    ) -> MenuNode:
        params = node.parameters
        target = node.bind.target

        if not isinstance(params, GizmoParameters):
            raise TypeError(
                f"Gizmo '{node.name}' expects GizmoParameters, got {type(params)}"
            )
        if not isinstance(target, CollectionTarget):
            raise TypeError(
                f"Gizmo '{node.name}' expects CollectionTarget, got {type(target)}"
            )

        capacity = params.capacity
        columns = params.columns
        gap = params.gap
        pane_id = params.pane
        button_id = params.button

        slot_props = properties.panes[pane_id]
        slot_w = slot_props.dimensions.w
        slot_l = slot_props.dimensions.l

        total_rows = (capacity + columns - 1) // columns
        row_w = columns * slot_w + (columns - 1) * gap
        row_l = slot_l
        grid_w = row_w
        grid_l = total_rows * slot_l + (total_rows - 1) * gap

        row_panes: List[MenuNode] = []

        for row_idx in range(total_rows):
            start_slot = row_idx * columns
            end_slot = min(start_slot + columns, capacity)
            slot_panes: List[MenuNode] = []

            for slot_idx in range(start_slot, end_slot):
                button_node = MenuNode(
                    id=button_id,
                    name=f"{node.name}-slot-{slot_idx}",
                    instance=AssetInstances.BUTTONS.value,
                    bind=MenuBinding(
                        schema=Bindings.SELECT.value,
                        target=SelectTarget(
                            selection=Selections.SLOT.value,
                            selector=node.name,
                            index=slot_idx
                        )
                    ),
                    parameters=ButtonParameters(status=Statuses.IDLE.value)
                )

                icon_node = MenuNode(
                    id=node.id,
                    name=f"{node.name}-icon-{slot_idx}",
                    instance=AssetInstances.ICONS.value,
                    bind=MenuBinding(
                        schema=Bindings.APERTURE.value,
                        target=ApertureTarget(
                            selector=node.name,
                            index=slot_idx
                        )
                    )
                )

                slot_container = MenuNode(
                    id=pane_id,
                    name=f"{node.name}-slot-{slot_idx}-pane",
                    instance=AssetInstances.PANES.value,
                    parameters=PaneParameters(
                        layout=Layouts.OVERLAY.value,
                        alignment=Alignments.CENTER.value,
                        gap=0,
                        margins=0,
                        dimensions=Dimensions(w=slot_w, l=slot_l),
                        children=[button_node, icon_node]
                    )
                )
                slot_panes.append(slot_container)

            row_pane = MenuNode(
                id=pane_id,
                name=f"{node.name}-row-{row_idx}",
                instance=AssetInstances.PANES.value,
                parameters=PaneParameters(
                    layout=Layouts.DOCK.value,
                    alignment=Alignments.START.value,
                    gap=gap,
                    margins=0,
                    dimensions=Dimensions(w=row_w, l=row_l),
                    children=slot_panes
                )
            )
            row_panes.append(row_pane)

        root_binding = MenuBinding(
            schema=Bindings.COLLECTION.value,
            target=CollectionTarget(
                source=target.source,
                capacity=capacity,
                columns=columns
            )
        )

        return MenuNode(
            id=pane_id,
            name=node.name,
            instance=AssetInstances.PANES.value,
            bind=root_binding,
            parameters=PaneParameters(
                layout=Layouts.STACK.value,
                alignment=Alignments.START.value,
                gap=gap,
                margins=0,
                dimensions=Dimensions(w=grid_w, l=grid_l),
                children=row_panes
            )
        )