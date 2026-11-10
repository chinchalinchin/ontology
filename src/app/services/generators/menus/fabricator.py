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
    AxisAlignment,
    MenuNode,
    PaneParameters,
    GizmoParameters,
    ButtonParameters,
    MenuBinding,
    CollectionTarget,
    SelectTarget,
    ApertureTarget
)
from app.models.menus import MenuContext

# Cython Libraries
from libs.core.models import Scale


class Fabricator:
    """
    Transforms declarative virtual MenuNode(instance="gizmos") into
    concrete MenuNode(instance="panes") subtrees based on binding schema.
    """

    @classmethod
    def expand(
        cls,
        node: MenuNode,
        context: MenuContext
    ) -> MenuNode:
        if not node.bind or not node.bind.schema:
            raise ValueError(f"Gizmo '{node.name}' declared without a binding schema.")

        handlers: Dict[str, Callable[
            [MenuNode, MenuContext], MenuNode
        ]] = {
            Bindings.COLLECTION.value: cls._collection,
        }

        handler = handlers.get(node.bind.schema)
        if not handler:
            raise NotImplementedError(
                f"Unsupported gizmo schema '{node.bind.schema}' for node '{node.name}'."
            )

        return handler(node, context)

    @classmethod
    def _collection(
        cls,
        node: MenuNode,
        context: MenuContext
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
        grid_scale = params.dimensions

        total_rows = (capacity + columns - 1) // columns
        row_scale = Scale(w=grid_scale.w, l=grid_scale.l / total_rows)
        slot_scale = Scale(w=grid_scale.w / columns, l=grid_scale.l / total_rows)

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
                        alignment=AxisAlignment(
                            horizontal=Alignments.CENTER.value,
                            vertical=Alignments.CENTER.value
                        ),
                        gap=0,
                        margins=0,
                        dimensions=slot_scale,
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
                    alignment=AxisAlignment(
                        horizontal=Alignments.START.value,
                        vertical=Alignments.CENTER.value
                    ),
                    gap=gap,
                    margins=0,
                    dimensions=row_scale,
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
                alignment=AxisAlignment(
                    horizontal=Alignments.START.value,
                    vertical=Alignments.CENTER.value
                ),
                gap=gap,
                margins=0,
                dimensions=grid_scale,
                children=row_panes
            )
        )