"""
# Ontology: tests.unit.fixtures.components

Mock application component fixtures
"""
# Standard Libraries
from unittest.mock import (
    MagicMock, 
)
import collections

# External Libraries
import pytest

# Application Libraries
from app.config.enums import (
    Relations
)
from app.game.devices import Keyboard
from app.game.board import Board
from app.game.engine import Engine
from app.game.screen import Screen
from app.game.logic.mechanics.world import SeasonMechanics
from app.models.state import CalendarState
from app.services.generators.game.factory import Factory
from app.services.translators import (
    LambdaTranslator,
    CompilerTranslator
)
from app.config.enums import Executors

# Cython Libraries
from libs.core.models import (
    Dimensions, 
    Position,
    Boundary
)

# ---------------------------------------------------------------------------
# ----------------------------------------------------------- MOCK COMPONENTS
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_screen(mock_registry, monkeypatch) -> Screen:
  monkeypatch.setattr(
      "app.game.screen.render.canvas", lambda w, l, opaque=False: MagicMock()
  )
  monkeypatch.setattr(
      "app.game.screen.render.construct", lambda canvas, tiles: None
  )
  monkeypatch.setattr("app.game.screen.render.clear", lambda: None)
  monkeypatch.setattr("app.game.screen.render.present", lambda: None)
  monkeypatch.setattr("app.game.screen.render.destroy", lambda canvas: None)
  monkeypatch.setattr(
      "app.game.screen.render.render", lambda *args, **kwargs: None
  )
  monkeypatch.setattr(
      "app.game.screen.render.superimpose", lambda *args, **kwargs: None
  )
  monkeypatch.setattr(
      "app.game.screen.render.channel", lambda *args, **kwargs: None
  )
  monkeypatch.setattr("app.game.screen.render.dim", lambda *args, **kwargs: None)

  screen = Screen(
      screensize=Dimensions(320, 240),
      boardsize=Dimensions(640, 480),
      tiles=[],
      registry=mock_registry,
      calendar=CalendarState(),
  )

  screen.cleared = False
  screen.presented = False
  screen.drawn_assets = []
  screen.reconstructed_tiles = []
  screen.reconstructed_calendar = None

  real_clear = screen.clear

  def _spy_clear():
    screen.cleared = True
    return real_clear()

  monkeypatch.setattr(screen, "clear", _spy_clear)

  real_present = screen.present

  def _spy_present():
    screen.presented = True
    return real_present()

  monkeypatch.setattr(screen, "present", _spy_present)

  real_draw = screen.draw

  def _spy_draw(assets, focus, dim):
    screen.drawn_assets = list(assets)
    return real_draw(assets, focus, dim)

  monkeypatch.setattr(screen, "draw", _spy_draw)

  real_reconstruct = screen.reconstruct

  def _spy_reconstruct(tiles, calendar):
    screen.reconstructed_tiles = list(tiles)
    screen.reconstructed_calendar = calendar
    return real_reconstruct(tiles, calendar)

  monkeypatch.setattr(screen, "reconstruct", _spy_reconstruct)

  return screen


@pytest.fixture
def mock_registry() -> MagicMock:
    registry = MagicMock()
    registry.image.side_effect = lambda key: (MagicMock(), 0, 0, 32, 32)
    return registry


@pytest.fixture
def mock_board(
    mock_assets, 
    mock_configurations, 
    mock_equipment,
    mock_cradle,
    mock_keyboard
) -> Board:    
    board = Board(
        assets=mock_assets, 
        configurations=mock_configurations, 
        equipment=mock_equipment
    )
    board.perimeters["0"] = [
        Boundary(Position(0, 0), Dimensions(320, 1)),
        Boundary(Position(0, 319), Dimensions(320, 1)),
        Boundary(Position(0, 0), Dimensions(1, 320)),
        Boundary(Position(319, 0), Dimensions(1, 320))
    ]
    board.set_cradle(mock_cradle)
    board.set_device(mock_keyboard)
    return board


@pytest.fixture
def mock_keyboard(
    mock_mapping_configuration
) -> Keyboard:
    return Keyboard(mock_mapping_configuration.keyboard)


@pytest.fixture
def mock_lambda_executors(
    mock_actuator,
    mock_configurations,
):
    translator = LambdaTranslator()
    intention_executor = translator.compile(mock_configurations.intentions)
    plot_executor = translator.compile(mock_configurations.plots)
    
    executors = {
        Executors.INTENTION.value: intention_executor,
        Executors.PLOT.value: plot_executor,
        Executors.ACTUATOR.value: mock_actuator
    }

    if mock_configurations.stages:
        for lifespan_key, rules in mock_configurations.stages.items():
            executors[lifespan_key] = translator.compile(rules)

    return executors

@pytest.fixture
def mock_compiler_executors(
    mock_actuator,
    mock_configurations,
):
    translator = CompilerTranslator()
    intention_executor = translator.compile(mock_configurations.intentions)
    plot_executor = translator.compile(mock_configurations.plots)
    
    executors = {
        Executors.INTENTION.value: intention_executor,
        Executors.PLOT.value: plot_executor,
        Executors.ACTUATOR.value: mock_actuator
    }

    if mock_configurations.stages:
        for lifespan_key, rules in mock_configurations.stages.items():
            executors[lifespan_key] = translator.compile(rules)

    return executors

@pytest.fixture
def mock_bus() -> collections.deque:
    return collections.deque()


@pytest.fixture
def mock_relations(mock_shoreline_index) -> dict:
    return {
        Relations.SHORELINES.value: mock_shoreline_index
    }


@pytest.fixture
def mock_engine_with_lambda_transitions(
    mock_board, 
    mock_mechanics_configuration,
    mock_lambda_executors,
    mock_relations,
    mock_provider
) -> Engine:
    """
    Fully constructs the Engine with live Mechanics and Executors
    """
    world_mechanics = [
        Factory.mechanics(m, mock_lambda_executors, mock_relations) 
        for m in mock_mechanics_configuration.world
    ]

    return Engine(
        board=mock_board,
        screens={},
        core=[],
        world=world_mechanics,
        provider=mock_provider
    )


@pytest.fixture
def mock_engine_with_compiler_transitions(
    mock_board, 
    mock_mechanics_configuration,
    mock_compiler_executors,
    mock_relations,
    mock_provider
) -> Engine:
    """
    Fully constructs the Engine with live Mechanics and Executors
    """  
    world_mechanics = [
        Factory.mechanics(m, mock_compiler_executors, mock_relations) 
        for m in mock_mechanics_configuration.world
    ]

    return Engine(
        board=mock_board,
        screens={},
        core=[],
        world=world_mechanics,
        provider=mock_provider
    )

@pytest.fixture
def mock_engine_core(
    mock_board,
    mock_screen,
    mock_provider
) -> Engine:
    """
    Constructs an Engine with a live Board, live buses, concrete handlers, and stubbed rendering.
    """

    return Engine(
        board=mock_board,
        screens={"0": mock_screen},
        core=[],
        world=[],
        provider=mock_provider
    )

@pytest.fixture
def mock_season_mechanics(mock_lambda_executors) -> SeasonMechanics:
  """Concrete SeasonMechanics instance pre-configured with compiled stage executors."""
  mechanic = SeasonMechanics()
  mechanic.executors = mock_lambda_executors
  return mechanic