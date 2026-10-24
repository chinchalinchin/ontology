"""
# Ontology: tests.test_cli.py

Unit tests for the ontology CLI tools.
"""
import sys
import os
import logging
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import cli

# ---------------------------------------------------------
# ARGUMENT PARSING TESTS
# ---------------------------------------------------------

@pytest.mark.cli
def test_arguments_start_defaults():
    test_args = ["cli.py", "start", "level_01"]
    
    with patch.object(sys, "argv", test_args):
        args = cli.arguments()
        
        assert args.command == "start"
        assert args.board_key == "level_01"
        assert args.width == 480
        assert args.height == 480
        assert args.device == "keyboard"
        assert args.log_level == "INFO"
        assert args.dump_state is False
        assert args.dump_menus is False
        assert args.dump_sdl is False
        assert args.dump_registry is False
        assert args.software is False
        assert args.instances is None
        assert args.categories is None
        assert args.ids is None
        assert args.names is None


@pytest.mark.cli
def test_arguments_filter_flags():
    test_args = [
        "cli.py", "--instances", "sprites,player", "--categories", "sheets,objects",
        "--ids", "jasilynn", "--names", "evil-.*",
        "start", "level_01"
    ]
    
    with patch.object(sys, "argv", test_args):
        args = cli.arguments()
        
        assert args.instances == "sprites,player"
        assert args.categories == "sheets,objects"
        assert args.ids == "jasilynn"
        assert args.names == "evil-.*"


@pytest.mark.cli
def test_arguments_prerender_flags():
    test_args = [
        "cli.py", "--log-level", "DEBUG", "--software", 
        "prerender", "level_01", "--out", "./out", "--layer", "background"
    ]
    
    with patch.object(sys, "argv", test_args):
        args = cli.arguments()
        
        assert args.command == "prerender"
        assert args.log_level == "DEBUG"
        assert args.software is True
        assert args.out == "./out"
        assert args.layer == "background"


@pytest.mark.cli
def test_arguments_map():
    test_args = ["cli.py", "map", "level_01", "--out", "./out", "--layer", "background"]
    
    with patch.object(sys, "argv", test_args):
        args = cli.arguments()
        
        assert args.command == "map"
        assert args.out == "./out"
        assert args.layer == "background"


@pytest.mark.cli
def test_arguments_missing_required():
    test_args = ["cli.py", "render", "level_01"]  # Missing --out and --layer
    
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            cli.arguments()
        assert exc_info.value.code == 2

# ---------------------------------------------------------
# ASSET FILTERING TESTS
# ---------------------------------------------------------

@pytest.mark.cli
def test_filter_assets_excludes_widgets(mock_assets, mock_widget):
    mixed_assets = mock_assets + [mock_widget]
    result = cli.filter_assets(mixed_assets)
    
    assert mock_widget not in result
    assert len(result) == len(mock_assets)


@pytest.mark.cli
def test_filter_assets_by_instance(mock_assets):
    # Single instance pattern
    sprites = cli.filter_assets(mock_assets, {"instances": "sprites"})
    assert len(sprites) > 0
    assert all(a.instance == "sprites" for a in sprites)
    
    # Comma-separated instances
    sprites_and_crates = cli.filter_assets(mock_assets, {"instances": "sprites,crates"})
    assert all(a.instance in ("sprites", "crates") for a in sprites_and_crates)
    assert any(a.instance == "sprites" for a in sprites_and_crates)
    assert any(a.instance == "crates" for a in sprites_and_crates)
    
    # Regex matching
    cr_instances = cli.filter_assets(mock_assets, {"instances": "^cr.*"})
    assert all(a.instance in ("crates", "crops") for a in cr_instances)


@pytest.mark.cli
def test_filter_assets_by_category(mock_assets):
    sheets = cli.filter_assets(mock_assets, {"categories": "sheets"})
    assert len(sheets) > 0
    assert all(a.category == "sheets" for a in sheets)


@pytest.mark.cli
def test_filter_assets_by_id_and_name(mock_assets):
    # Match ID
    jasilynn = cli.filter_assets(mock_assets, {"ids": "jasilynn"})
    assert len(jasilynn) == 1
    assert jasilynn[0].id == "jasilynn"
    
    # Match Name regex
    npc = cli.filter_assets(mock_assets, {"names": "evil-empress-.*"})
    assert len(npc) == 1
    assert npc[0].name == "evil-empress-jasilynn"


@pytest.mark.cli
def test_filter_assets_conjunction(mock_assets):
    # Conjunction of category and instance
    matched = cli.filter_assets(mock_assets, {"categories": "sheets", "instances": "players"})
    assert len(matched) == 1
    assert matched[0].instance == "players"
    assert matched[0].category == "sheets"
    
    # Non-intersecting criteria yields empty result
    no_match = cli.filter_assets(mock_assets, {"categories": "objects", "instances": "players"})
    assert len(no_match) == 0


@pytest.mark.cli
def test_filter_assets_no_match(mock_assets):
    result = cli.filter_assets(mock_assets, {"ids": "non_existent_key_12345"})
    assert result == []

# ---------------------------------------------------------
# DUMP FUNCTION TESTS
# ---------------------------------------------------------

@pytest.mark.cli
@patch("cli.datetime")
@patch("cli.settings")
def test_dump_state_success(mock_settings, mock_datetime, mock_board):
    mock_datetime.datetime.now.return_value.strftime.return_value = "20260101_120000"
    mock_settings.TEMPLATE_DIR = Path("/mock/dir")
    mock_settings.DUMP_TEMPLATES = {"state": "state_template.md"}
    mock_settings.DUMP_DIR = Path("/mock/dump")
    
    mock_template_str = "Template: {{ board_key }} {{ timestamp }}"
    
    with patch("pathlib.Path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=mock_template_str)) as mocked_file, \
         patch("cli.jinja2.Template.render", return_value="Rendered Output") as mock_render:
         
        cli.dump("level_01", mock_board, "state")
        
        mock_render.assert_called_once_with(
            board_key="level_01", 
            timestamp="20260101_120000",
            assets=mock_board.assets(),
            perimeters=mock_board.perimeters,
            calendar=mock_board.calendar,
            plot=mock_board.plot
        )
        assert mocked_file.call_count == 2
        mocked_file().write.assert_called_once_with("Rendered Output")


@pytest.mark.cli
@patch("cli.datetime")
@patch("cli.settings")
def test_dump_state_with_filters(mock_settings, mock_datetime, mock_board):
    mock_datetime.datetime.now.return_value.strftime.return_value = "20260101_120000"
    mock_settings.TEMPLATE_DIR = Path("/mock/dir")
    mock_settings.DUMP_TEMPLATES = {"state": "state_template.md"}
    mock_settings.DUMP_DIR = Path("/mock/dump")
    
    mock_template_str = "Template: {{ board_key }} {{ timestamp }}"
    filters = {"categories": "sheets", "instances": "players"}
    
    with patch("pathlib.Path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=mock_template_str)), \
         patch("cli.jinja2.Template.render", return_value="Rendered Output") as mock_render:
         
        cli.dump("level_01", mock_board, "state", filters=filters)
        
        expected_assets = [
            a for a in mock_board.assets() 
            if a.category == "sheets" and a.instance == "players"
        ]
        mock_render.assert_called_once_with(
            board_key="level_01", 
            timestamp="20260101_120000",
            assets=expected_assets,
            perimeters=mock_board.perimeters,
            calendar=mock_board.calendar,
            plot=mock_board.plot
        )


@pytest.mark.cli
@patch("cli.datetime")
@patch("cli.settings")
def test_dump_menus_success(mock_settings, mock_datetime, mock_board):
    mock_datetime.datetime.now.return_value.strftime.return_value = "20260101_120000"
    mock_settings.TEMPLATE_DIR = Path("/mock/dir")
    mock_settings.DUMP_TEMPLATES = {"menus": "menus_template.md"}
    mock_settings.DUMP_DIR = Path("/mock/dump")
    
    mock_board.menus = ["menu1"]
    mock_board.overlays = ["overlay1"]

    mock_template_str = "Template: {{ board_key }} {{ timestamp }}"
    
    with patch("pathlib.Path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=mock_template_str)) as mocked_file, \
         patch("cli.jinja2.Template.render", return_value="Rendered Output") as mock_render:
         
        cli.dump("level_01", mock_board, "menus")
        
        mock_render.assert_called_once_with(
            board_key="level_01", 
            timestamp="20260101_120000",
            menus=["menu1"],
            overlays=["overlay1"]
        )
        assert mocked_file.call_count == 2
        mocked_file().write.assert_called_once_with("Rendered Output")


@pytest.mark.cli
@patch("cli.datetime")
@patch("cli.settings")
@patch("cli.sysinfo")
def test_dump_sdl_success(mock_sys_info, mock_settings, mock_datetime, mock_board):
    mock_datetime.datetime.now.return_value.strftime.return_value = "20260101_120000"
    mock_settings.TEMPLATE_DIR = Path("/mock/dir")
    mock_settings.DUMP_TEMPLATES = {"sdl": "sdl_template.md"}
    mock_settings.DUMP_DIR = Path("/mock/dump")
    mock_sys_info.return_value = {"os": "Linux", "renderer": "opengl"}
    
    with patch("pathlib.Path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data="")) as mocked_file, \
         patch("cli.jinja2.Template.render", return_value="Output") as mock_render:
         
        cli.dump("level_01", mock_board, "sdl")
        
        mock_render.assert_called_once_with(
            board_key="level_01", 
            timestamp="20260101_120000",
            sys_info={"os": "Linux", "renderer": "opengl"}
        )


@pytest.mark.cli
@patch("cli.datetime")
@patch("cli.settings")
def test_dump_registry_success(mock_settings, mock_datetime):
    mock_datetime.datetime.now.return_value.strftime.return_value = "20260101_120000"
    mock_settings.TEMPLATE_DIR = Path("/mock/dir")
    mock_settings.DUMP_TEMPLATES = {"registry": "registry_template.md"}
    mock_settings.DUMP_DIR = Path("/mock/dump")
    
    mock_screen = MagicMock()
    mock_screen.registry._frames = {"frame_1": ("item_1", 0, 0, 32, 32)}
    mock_screen.registry._textures = {"tex_1": "pointer"}
    
    mock_engine = MagicMock()
    mock_engine.screens = {"layer_0": mock_screen}
    
    with patch("pathlib.Path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data="")) as mocked_file, \
         patch("cli.jinja2.Template.render", return_value="Output") as mock_render:
         
        cli.dump("level_01", mock_engine, "registry")
        
        mock_render.assert_called_once_with(
            board_key="level_01", 
            timestamp="20260101_120000",
            textures=["tex_1"],
            frames={"frame_1": {"item_id": "item_1", "crop_x": 0, "crop_y": 0, "crop_w": 32, "crop_l": 32}}
        )


@pytest.mark.cli
@patch("cli.settings")
def test_dump_missing_template(mock_settings, mock_board, caplog):
    mock_settings.TEMPLATE_DIR = Path("/mock/dir")
    mock_settings.DUMP_TEMPLATES = {"state": "state_template.md"}
    
    with patch("pathlib.Path.exists", return_value=False):
        cli.dump("level_01", mock_board, "state")
        assert "Dump template not found" in caplog.text

# ---------------------------------------------------------
# HYDRATION TESTS
# ---------------------------------------------------------

@pytest.mark.cli
@patch("cli.Screen")
def test_force_hydration(mock_screen_class):
    mock_engine = MagicMock()
    
    # 1. Setup Migrator
    mock_migrator = MagicMock()
    mock_migrator.step.side_effect = [False, False, True]
    mock_engine.board.migrator = mock_migrator
    
    # 2. Setup Registry prewarming
    mock_registry = MagicMock()
    mock_registry.prewarm.side_effect = [False, True]
    
    # 3. Setup Screens and Board data
    mock_old_screen = MagicMock()
    mock_old_screen.registry = mock_registry
    mock_engine.screens = {"layer_0": mock_old_screen}
    
    mock_engine.board.layers.return_value = ["layer_0", "layer_1"]
    mock_engine.board.categories.return_value = ["tile_asset_1"]
    mock_engine.board.size.return_value = [MagicMock()]
    mock_screensize = MagicMock()
    
    # Execute
    cli.hydrate(mock_engine, "level_01", mock_screensize)
    
    # Assertions
    assert mock_migrator.step.call_count == 3
    assert mock_registry.prewarm.call_count == 2
    
    mock_old_screen.rebake.assert_called_once()
    assert mock_engine.screens["layer_0"] == mock_old_screen
    
    mock_screen_class.assert_called_once()
    assert mock_engine.screens["layer_1"] == mock_screen_class.return_value
    
    assert mock_engine.board.loaded is True

# ---------------------------------------------------------
# HANDLER TESTS
# ---------------------------------------------------------

@pytest.mark.cli
@patch("cli.hydrate")
def test_handle_prerender_success(mock_force_hydration):
    args = MagicMock(board_key="level_01", device="keyboard", layer="bg", out="/tmp/out")
    screensize = MagicMock()
    
    mock_orchestrator = MagicMock()
    mock_engine = MagicMock()
    mock_screen = MagicMock()
    
    mock_orchestrator.orchestrate.return_value = mock_engine
    mock_engine.screens = {"bg": mock_screen}
    
    with patch("pathlib.Path.mkdir") as mock_mkdir:
        engine = cli.handle_prerender(args, mock_orchestrator, screensize)
        
        mock_force_hydration.assert_called_once_with(mock_engine, "level_01", screensize)
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_screen.export_background.assert_called_once()
        
        assert engine == mock_engine


@pytest.mark.cli
@patch("cli.hydrate")
def test_handle_render_success(mock_force_hydration):
    args = MagicMock(board_key="level_01", device="keyboard", layer="bg", out="/tmp/out")
    screensize = MagicMock()
    
    mock_orchestrator = MagicMock()
    mock_engine = MagicMock()
    mock_screen = MagicMock()
    
    mock_orchestrator.orchestrate.return_value = mock_engine
    mock_engine.screens = {"bg": mock_screen}
    mock_engine.board.renderables.return_value = ["asset1", "asset2"]
    
    mock_player = MagicMock()
    mock_player.state.position = MagicMock()
    mock_player.dimensions = MagicMock()
    mock_engine.board.player.return_value = mock_player
    
    with patch("pathlib.Path.mkdir") as mock_mkdir:
        engine = cli.handle_render(args, mock_orchestrator, screensize)
        
        mock_force_hydration.assert_called_once_with(mock_engine, "level_01", screensize)
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        
        mock_screen.export_render.assert_called_once_with(
            "/tmp/out/level_01-bg.png", 
            ["asset1", "asset2"], 
            mock_player.state.position, 
            mock_player.dimensions
        )
        assert engine == mock_engine


@pytest.mark.cli
@patch("cli.hydrate")
def test_handle_render_full_success(mock_force_hydration):
    args = MagicMock(board_key="level_01", device="keyboard", layer="bg", out="/tmp/out")
    screensize = MagicMock()
    
    mock_orchestrator = MagicMock()
    mock_engine = MagicMock()
    mock_screen = MagicMock()
    
    mock_orchestrator.orchestrate.return_value = mock_engine
    mock_engine.screens = {"bg": mock_screen}
    mock_engine.board.renderables.return_value = ["asset1", "asset2"]
    
    with patch("pathlib.Path.mkdir") as mock_mkdir:
        engine = cli.handle_map(args, mock_orchestrator, screensize)
        
        mock_force_hydration.assert_called_once_with(mock_engine, "level_01", screensize)
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        
        mock_screen.export_map.assert_called_once_with(
            "/tmp/out/level_01-bg-full.png", 
            ["asset1", "asset2"]
        )
        assert engine == mock_engine


@pytest.mark.cli
@patch("cli.hydrate")
def test_handle_render_missing_layer(mock_force_hydration, caplog):
    args = MagicMock(board_key="level_01", device="keyboard", layer="invalid_layer", out="/tmp/out")
    screensize = MagicMock()
    
    mock_orchestrator = MagicMock()
    mock_engine = MagicMock()
    mock_orchestrator.orchestrate.return_value = mock_engine
    mock_engine.screens = {"bg": MagicMock()}
    
    engine = cli.handle_render(args, mock_orchestrator, screensize)
    
    assert "Layer 'invalid_layer' not found" in caplog.text
    assert engine == mock_engine


@pytest.mark.cli
def test_handle_start_keyboard_interrupt(caplog):
    caplog.set_level(logging.INFO)
    
    args = MagicMock(board_key="level_01", device="keyboard", dump_sdl=False, dump_registry=False)
    screensize = MagicMock()
    
    mock_orchestrator = MagicMock()
    mock_engine = MagicMock()
    mock_orchestrator.orchestrate.return_value = mock_engine
    
    mock_engine.start.side_effect = KeyboardInterrupt()
    
    engine = cli.handle_start(args, mock_orchestrator, screensize)
    
    assert "Game engine loop interrupted by user." in caplog.text
    assert engine == mock_engine

# ---------------------------------------------------------
# MAIN EXECUTION TESTS
# ---------------------------------------------------------

@pytest.mark.cli
@patch("cli.Orchestrator")
@patch("cli.quit_sdl")
@patch("cli.gc.collect")
@patch.dict(os.environ, {}, clear=True)
def test_main_software_flag(mock_gc, mock_quit_sdl, mock_orchestrator_class):
    test_args = ["cli.py", "--software", "start", "level_01"]
    
    mock_handler = MagicMock()
    
    with patch.object(sys, "argv", test_args), \
         patch.dict("cli.COMMAND_REGISTRY", {"start": mock_handler}):
        
        cli.main()
        
        assert os.environ.get("SDL_RENDER_DRIVER") == "software"
        mock_handler.assert_called_once()
        mock_gc.assert_called_once()
        mock_quit_sdl.assert_called_once()


@pytest.mark.cli
@patch("cli.Orchestrator")
@patch("cli.quit_sdl")
def test_main_dump_flags(mock_quit, mock_orchestrator):
    test_args = [
        "cli.py", "--dump-state", "--dump-menus", "--dump-sdl", "--dump-registry", 
        "prerender", "level_01", "--out", "./out", "--layer", "bg"
    ]
    
    mock_handler = MagicMock()
    
    with patch.object(sys, "argv", test_args), \
         patch.dict("cli.COMMAND_REGISTRY", {"prerender": mock_handler}), \
         patch("cli.dump") as mock_dump:
        
        cli.main()
        
        assert mock_dump.call_count == 4
        
        mock_engine = mock_handler.return_value
        expected_filters = {
            "instances": None,
            "categories": None,
            "ids": None,
            "names": None
        }
        
        mock_dump.assert_any_call("level_01", mock_engine.board, "state", filters=expected_filters)
        mock_dump.assert_any_call("level_01", mock_engine.board, "menus")
        mock_dump.assert_any_call("level_01", mock_engine.board, "sdl")


@pytest.mark.cli
@patch("cli.Orchestrator")
@patch("cli.quit_sdl")
def test_main_dump_with_filter_flags(mock_quit, mock_orchestrator):
    test_args = [
        "cli.py", "--dump-state", "--instances", "sprites,player", "--categories", "sheets",
        "prerender", "level_01", "--out", "./out", "--layer", "bg"
    ]
    
    mock_handler = MagicMock()
    
    with patch.object(sys, "argv", test_args), \
         patch.dict("cli.COMMAND_REGISTRY", {"prerender": mock_handler}), \
         patch("cli.dump") as mock_dump:
        
        cli.main()
        
        mock_engine = mock_handler.return_value
        expected_filters = {
            "instances": "sprites,player",
            "categories": "sheets",
            "ids": None,
            "names": None
        }
        mock_dump.assert_called_once_with("level_01", mock_engine.board, "state", filters=expected_filters)


@pytest.mark.cli
@patch("cli.configure_logging")
@patch("cli.arguments")
def test_main_unknown_command(mock_arguments, mock_configure_logging, caplog):
    mock_args = MagicMock(command="invalid_cmd", log_level="INFO", software=False)
    mock_arguments.return_value = mock_args
    
    with patch("cli.Orchestrator"):
        with pytest.raises(SystemExit) as exc_info:
            cli.main()
            
        assert exc_info.value.code == 1
        assert "Unknown command received: invalid_cmd" in caplog.text