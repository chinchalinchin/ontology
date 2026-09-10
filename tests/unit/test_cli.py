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

def test_arguments_missing_required():
    test_args = ["cli.py", "render", "level_01"]  # Missing --out and --layer
    
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exc_info:
            cli.arguments()
        assert exc_info.value.code == 2

# ---------------------------------------------------------
# DUMP FUNCTION TESTS
# ---------------------------------------------------------

@patch("cli.datetime")
@patch("cli.settings")
def test_dump_state_success(mock_settings, mock_datetime):
    # Setup mocks
    mock_datetime.datetime.now.return_value.strftime.return_value = "20260101_120000"
    mock_settings.TEMPLATE_DIR = Path("/mock/dir")
    mock_settings.DUMP_TEMPLATES = {"state": "state_template.md"}
    
    mock_board = MagicMock()
    mock_board.assets.return_value = ["asset1", "asset2"]
    mock_board.perimeters.return_value = {"layer_0": [{"mock": "bounds"}]}

    mock_template_str = "Template: {{ board_key }} {{ timestamp }}"
    
    with patch("pathlib.Path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=mock_template_str)) as mocked_file, \
         patch("cli.jinja2.Template.render", return_value="Rendered Output") as mock_render:
         
        cli.dump("level_01", mock_board, "state")
        
        # Verify render was called with correct state arguments
        mock_render.assert_called_once_with(
            board_key="level_01", 
            timestamp="20260101_120000",
            assets=["asset1", "asset2"],
            perimeters={"layer_0": [{"mock": "bounds"}]}
        )
        
        # Verify file writes
        assert mocked_file.call_count == 2
        mocked_file().write.assert_called_once_with("Rendered Output")

@patch("cli.datetime")
@patch("cli.settings")
def test_dump_menus_success(mock_settings, mock_datetime):
    # Setup mocks
    mock_datetime.datetime.now.return_value.strftime.return_value = "20260101_120000"
    mock_settings.TEMPLATE_DIR = Path("/mock/dir")
    mock_settings.DUMP_TEMPLATES = {"menus": "menus_template.md"}
    
    mock_board = MagicMock()
    mock_board.menus = ["menu1"]
    mock_board.overlays = ["overlay1"]

    mock_template_str = "Template: {{ board_key }} {{ timestamp }}"
    
    with patch("pathlib.Path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=mock_template_str)) as mocked_file, \
         patch("cli.jinja2.Template.render", return_value="Rendered Output") as mock_render:
         
        cli.dump("level_01", mock_board, "menus")
        
        # Verify render was called with correct menu arguments
        mock_render.assert_called_once_with(
            board_key="level_01", 
            timestamp="20260101_120000",
            menus=["menu1"],
            overlays=["overlay1"]
        )
        
        assert mocked_file.call_count == 2
        mocked_file().write.assert_called_once_with("Rendered Output")

@patch("cli.datetime")
@patch("cli.settings")
@patch("cli.get_system_info")
def test_dump_sdl_success(mock_sys_info, mock_settings, mock_datetime):
    mock_datetime.datetime.now.return_value.strftime.return_value = "20260101_120000"
    mock_settings.TEMPLATE_DIR = Path("/mock/dir")
    mock_sys_info.return_value = {"os": "Linux", "renderer": "opengl"}
    
    mock_board = MagicMock()
    
    with patch("pathlib.Path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data="")) as mocked_file, \
         patch("cli.jinja2.Template.render", return_value="Output") as mock_render:
         
        cli.dump("level_01", mock_board, "sdl")
        
        mock_render.assert_called_once_with(
            board_key="level_01", 
            timestamp="20260101_120000",
            sys_info={"os": "Linux", "renderer": "opengl"}
        )

@patch("cli.datetime")
@patch("cli.settings")
def test_dump_registry_success(mock_settings, mock_datetime):
    mock_datetime.datetime.now.return_value.strftime.return_value = "20260101_120000"
    mock_settings.TEMPLATE_DIR = Path("/mock/dir")
    
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

@patch("cli.settings")
def test_dump_missing_template(mock_settings, caplog):
    mock_settings.TEMPLATE_DIR = Path("/mock/dir")
    mock_settings.DUMP_TEMPLATES = {"state": "state_template.md"}
    
    with patch("pathlib.Path.exists", return_value=False):
        cli.dump("level_01", MagicMock(), "state")
        
        assert "Dump template not found" in caplog.text

# ---------------------------------------------------------
# HANDLER TESTS
# ---------------------------------------------------------

def test_handle_prerender_success():
    args = MagicMock(board_key="level_01", device="keyboard", layer="bg", out="/tmp/out")
    screensize = MagicMock()
    
    mock_orchestrator = MagicMock()
    mock_engine = MagicMock()
    mock_screen = MagicMock()
    
    mock_orchestrator.orchestrate.return_value = mock_engine
    mock_engine.screens = {"bg": mock_screen}
    
    with patch("pathlib.Path.mkdir") as mock_mkdir:
        engine = cli.handle_prerender(args, mock_orchestrator, screensize)
        
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_screen.export_background.assert_called_once()
        
        assert engine == mock_engine

def test_handle_render_missing_layer(caplog):
    args = MagicMock(board_key="level_01", device="keyboard", layer="invalid_layer", out="/tmp/out")
    screensize = MagicMock()
    
    mock_orchestrator = MagicMock()
    mock_engine = MagicMock()
    mock_orchestrator.orchestrate.return_value = mock_engine
    mock_engine.screens = {"bg": MagicMock()} # "invalid_layer" is missing
    
    engine = cli.handle_render(args, mock_orchestrator, screensize)
    
    assert "Layer 'invalid_layer' not found" in caplog.text
    assert engine == mock_engine

def test_handle_start_keyboard_interrupt(caplog):
    caplog.set_level(logging.INFO)
    
    args = MagicMock(board_key="level_01", device="keyboard", dump_sdl=False, dump_registry=False)
    screensize = MagicMock()
    
    mock_orchestrator = MagicMock()
    mock_engine = MagicMock()
    mock_orchestrator.orchestrate.return_value = mock_engine
    
    # Simulate user pressing Ctrl+C during the game loop
    mock_engine.start.side_effect = KeyboardInterrupt()
    
    engine = cli.handle_start(args, mock_orchestrator, screensize)
    
    assert "Game engine loop interrupted by user." in caplog.text
    assert engine == mock_engine

# ---------------------------------------------------------
# MAIN EXECUTION TESTS
# ---------------------------------------------------------

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
        
        # Verify SDL environment variable was injected
        assert os.environ.get("SDL_RENDER_DRIVER") == "software"
        
        # Verify dispatcher routing
        mock_handler.assert_called_once()
        
        # Verify cleanup routine
        mock_gc.assert_called_once()
        mock_quit_sdl.assert_called_once()

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
        
        # Verify all types of dumps were requested post-execution 
        assert mock_dump.call_count == 4
        
        # Extract engine to assert context routing
        mock_engine = mock_handler.return_value
        
        mock_dump.assert_any_call("level_01", mock_engine.board, 'state')
        mock_dump.assert_any_call("level_01", mock_engine.board, 'menus')
        mock_dump.assert_any_call("level_01", mock_engine.board, 'sdl')
        mock_dump.assert_any_call("level_01", mock_engine, 'registry')

@patch("cli.configure_logging")
@patch("cli.arguments")
def test_main_unknown_command(mock_arguments, mock_configure_logging, caplog):
    # Simulate an argument parse that somehow bypasses argparse choices
    mock_args = MagicMock(command="invalid_cmd", log_level="INFO", software=False)
    mock_arguments.return_value = mock_args
    
    with patch("cli.Orchestrator"):
        with pytest.raises(SystemExit) as exc_info:
            cli.main()
            
        assert exc_info.value.code == 1
        assert "Unknown command received: invalid_cmd" in caplog.text