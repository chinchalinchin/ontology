"""
@domain.test
@test.fixtures

# Ontology: Test - tests.unit.fixtures.menus

Loader-backed Menu, Binding, Layout, Context, and EventData fixtures.
"""
# Standard Libraries
import collections
from typing import Optional

# External Libraries
import pytest

# Application Libraries
from app.game.board import Board
from app.game.menus.core import (
    EventData,
    Menu,
)
from app.game.screen import Screen
from app.models.config import ConfigurationSchema
from app.models.config.menus import (
    ApertureTarget,
    CollectionTarget,
    GizmoParameters,
    IconTarget,
    LibraryTarget,
    MenuBinding,
    MenuNode,
    MeterTarget,
    SelectTarget,
    TextTarget,
)
from app.models.menus import (
    DialogueContext,
    InventoryContext,
    LoadContext,
    MainContext,
    MenuContext,
    PauseContext,
    TextContext,
    ViewContext,
)
from app.models.state import CollectionState
from app.services.generators.menus import Provider
from app.services.generators.menus import Layout
from app.services.orchestration import Migrator
from app.static.semantics import (
    AssetInstances,
    Bindings,
    Menus,
    Selections,
    Shortcuts,
)

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Scale,
)
from libs.graphics.registry import Registry

# -----------------------------------------------------------------------------
# --------------------------------------------------------------- MOCK BINDINGS
# -----------------------------------------------------------------------------


@pytest.fixture
def mock_library_bind() -> MenuBinding:
    return MenuBinding(
        schema=Bindings.LIBRARY.value,
        target=LibraryTarget(
            plot="context.plot.current",
            persona="context.sprite.psyche.persona",
            lexicon="context.sprite.psyche.dialogue",
        ),
    )


@pytest.fixture
def mock_text_bind() -> MenuBinding:
    return MenuBinding(
        schema=Bindings.TEXT.value,
        target=TextTarget(content="context.content"),
    )


@pytest.fixture
def mock_meter_bind() -> MenuBinding:
    return MenuBinding(
        schema=Bindings.METER.value,
        target=MeterTarget(meter="context.sprite.meters.health"),
    )


@pytest.fixture
def mock_icon_bind() -> MenuBinding:
    return MenuBinding(
        schema=Bindings.ICON.value,
        target=IconTarget(icon="context.sprite.slots.equipment.weapon"),
    )


@pytest.fixture
def mock_select_bind() -> MenuBinding:
    return MenuBinding(
        schema=Bindings.SELECT.value,
        target=SelectTarget(
            selection=Selections.SCROLLUP.value,
            selector="character-speech",
        ),
    )


@pytest.fixture
def mock_collection_bind() -> MenuBinding:
    return MenuBinding(
        schema=Bindings.COLLECTION.value,
        target=CollectionTarget(
            source="context.inventory.pack",
            capacity=8,
            columns=4,
        ),
    )


@pytest.fixture
def mock_aperture_bind() -> MenuBinding:
    return MenuBinding(
        schema=Bindings.APERTURE.value,
        target=ApertureTarget(
            selector="inventory-pack-grid",
            index=0,
        ),
    )


@pytest.fixture
def mock_aperture_bind_alt() -> MenuBinding:
    return MenuBinding(
        schema=Bindings.APERTURE.value,
        target=ApertureTarget(
            selector="inventory-pack-grid",
            index=5,
        ),
    )


# -----------------------------------------------------------------------------
# ---------------------------------------------------------- MOCK CONFIGURATION
# -----------------------------------------------------------------------------


@pytest.fixture
def mock_gizmo_node(mock_collection_bind: MenuBinding) -> MenuNode:
    return MenuNode(
        id="weapons",
        name="inventory-pack-grid",
        instance=Shortcuts.GIZMOS.value,
        bind=mock_collection_bind,
        parameters=GizmoParameters(
            capacity=8,
            columns=4,
            pane="transparent",
            button="slot",
            dimensions=Scale(0.60, 0.30),
            gap=5,
        ),
    )


# -----------------------------------------------------------------------------
# ----------------------------------------------------------------- MOCK STATES
# -----------------------------------------------------------------------------


@pytest.fixture
def mock_collection_state() -> CollectionState:
    return CollectionState(
        id="transparent",
        name="inventory-pack-grid",
        collection_function=lambda: ["shortsword", "dagger", "buckler"],
        capacity=8,
        columns=4,
        offset=0,
    )


# -----------------------------------------------------------------------------
# --------------------------------------------- MENU CONTEXTS, LAYOUT & FACTORY
# -----------------------------------------------------------------------------


@pytest.fixture
def mock_layout(mock_screen: Screen) -> Layout:
    return Layout(mock_screen.screensize)


@pytest.fixture
def mock_menu_context(
    mock_board: Board,
    mock_registry: Registry,
    mock_screen: Screen,
):
    """
    Fixture factory constructing a domain-hydrated MenuContext for any Menu key.
    """
    def _context(menu_id: str = Menus.MAIN.value) -> MenuContext:
        player = mock_board.player()
        sprites = mock_board.instances(AssetInstances.SPRITES.value)
        signs = mock_board.instances(AssetInstances.SIGNS.value)

        if menu_id == Menus.MAIN.value:
            return MainContext(registry=mock_registry)
        if menu_id == Menus.LOAD.value:
            return LoadContext(
                registry=mock_registry,
                screens={layer: mock_screen for layer in mock_board.layers()} or {"0": mock_screen},
                screensize=mock_screen.screensize,
            )
        if menu_id == Menus.VIEW.value:
            return ViewContext(sprite=player.state)
        if menu_id == Menus.DIALOGUE.value:
            speaker = sprites[0].state if sprites else player.state
            sign = signs[0].state if signs else None
            return DialogueContext(
                plot=mock_board.plot,
                sprite=speaker,
                object=sign,
            )
        if menu_id in (
            Menus.EQUIPMENT.value,
            Menus.POUCH.value,
            Menus.PACK.value,
            Menus.INVENTORY.value,
        ):
            return InventoryContext(
                inventory=player.state.inventory,
                slots=player.state.slots,
            )
        if menu_id == Menus.PAUSE.value:
            return PauseContext(board=mock_board)
        if menu_id == Menus.TEXT.value:
            return TextContext(content="One two three four five six seven eight.")
        return MenuContext()

    return _context


@pytest.fixture
def mock_menu(
    mock_provider: Provider,
    mock_configurations_schema: ConfigurationSchema,
    mock_menu_context,
    mock_screen: Screen,
):
    """
    Fixture factory unpacking a live Menu instance from YAML configuration via Provider.
    """
    def _menu(
        menu_id: str = Menus.MAIN.value,
        context: Optional[MenuContext] = None,
        screensize: Optional[Dimensions] = None,
    ) -> Menu:
        cfg = mock_configurations_schema.menus[menu_id]
        resolved_context = context if context is not None else mock_menu_context(menu_id)
        resolved_size = screensize if screensize is not None else mock_screen.screensize
        return mock_provider.unpack(
            menu_id,
            cfg,
            resolved_context,
            resolved_size,
        )

    return _menu


@pytest.fixture
def mock_event_data(
    mock_board: Board,
    mock_screen: Screen,
    mock_provider: Provider,
    mock_migrator: Migrator,
    mock_bus: collections.deque,
) -> EventData:
    """
    Hydrated EventData container wired with live Board, Screen, Provider, Migrator, and Bus.
    """
    screens = {layer: mock_screen for layer in mock_board.layers()}
    if not screens:
        screens["0"] = mock_screen
    mock_board.loaded = True
    return EventData(
        board=mock_board,
        screens=screens,
        provider=mock_provider,
        bus=mock_bus,
    )