"""
@domain.test
@test.unit
@workflow.cli

# Ontology: Tests - tests.unit.cli.test_cli

Unit tests for CLI argument parsing, utilities, command handlers, and main entrypoint.
"""
# Standard Libraries
import argparse
import json
import logging
import os
import sys
from pathlib import Path

# External Libraries
import pytest
import yaml

# CLI Libraries
import main
import cli.arguments as arguments
import cli.handlers as handlers
import cli.utilities as utilities
from cli.semantics import (
    Commands,
    Dumps,
    Filters,
)

# Application Libraries
from app.assets.base import Taxonomy
from app.models.state import StateSchema
from app.static.semantics import (
    AssetCategories,
    AssetInstances,
    Devices,
)

# Cython Libraries
from libs.core.models import (
    Dimensions,
    Position,
)

# ---------------------------------------------------------------------------

pytestmark = [
    pytest.mark.workflow_cli,
]

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------- ARGUMENTS
# ---------------------------------------------------------------------------


def test_arguments_start_defaults(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(sys, "argv", ["main.py", "start", "world-testbed"])

    args = arguments.construct(tmp_path)

    assert args.command == Commands.START.value
    assert args.board == "world-testbed"
    assert args.width == arguments.SCREENSIZE
    assert args.length == arguments.SCREENSIZE
    assert args.device == Devices.KEYBOARD.value
    assert args.log_level == "INFO"
    assert args.software is False
    assert args.dump_state is False
    assert args.dump_menus is False
    assert args.dump_sdl is False
    assert args.dump_registry is False


def test_arguments_start_optional_board(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(sys, "argv", ["main.py", "start"])

    args = arguments.construct(tmp_path)

    assert args.command == Commands.START.value
    assert args.board is None


def test_arguments_filter_flags(monkeypatch, tmp_path: Path):
    test_args = [
        "main.py",
        "--instance", "sprites,players",
        "--category", "sheets,objects",
        "--id", "jasilynn",
        "--name", "test-.*",
        "start",
        "world-testbed",
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    args = arguments.construct(tmp_path)

    assert args.instance == "sprites,players"
    assert args.category == "sheets,objects"
    assert args.id == "jasilynn"
    assert args.name == "test-.*"


def test_arguments_prerender_flags(monkeypatch, tmp_path: Path):
    test_args = [
        "main.py",
        "--log-level", "DEBUG",
        "--software",
        "prerender",
        "world-testbed",
        "--out", "./out",
        "--layer", "0",
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    args = arguments.construct(tmp_path)

    assert args.command == Commands.PRERENDER.value
    assert args.log_level == "DEBUG"
    assert args.software is True
    assert args.board == "world-testbed"
    assert args.out == "./out"
    assert args.layer == "0"


def test_arguments_map(monkeypatch, tmp_path: Path):
    test_args = [
        "main.py",
        "map",
        "world-testbed",
        "--out", "./out",
        "--layer", "0",
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    args = arguments.construct(tmp_path)

    assert args.command == Commands.MAP.value
    assert args.board == "world-testbed"
    assert args.out == "./out"
    assert args.layer == "0"


def test_arguments_schema_and_tags(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", "schema", "--target", "state", "--format", "json", "--out", "out.json"],
    )
    schema_args = arguments.construct(tmp_path)

    assert schema_args.command == Commands.SCHEMA.value
    assert schema_args.target == "state"
    assert schema_args.format == "json"
    assert schema_args.out == "out.json"

    monkeypatch.setattr(sys, "argv", ["main.py", "tags"])
    tags_args = arguments.construct(tmp_path)

    assert tags_args.command == Commands.TAGS.value
    assert tags_args.directory == tmp_path


def test_arguments_missing_required(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(sys, "argv", ["main.py", "render", "world-testbed"])

    with pytest.raises(SystemExit):
        arguments.construct(tmp_path)


# ---------------------------------------------------------------------------
# --------------------------------------------------------- UTILITIES: FILTER
# ---------------------------------------------------------------------------


def test_filter_assets_excludes_widgets(mock_assets, mock_asset):
    widget_asset = mock_asset(
        AssetCategories.OBJECTS.value,
        AssetInstances.CRATES.value,
    )
    widget_asset.taxonomy = Taxonomy(
        id="button",
        name="test-widget",
        category=AssetCategories.WIDGETS.value,
        instance=AssetInstances.BUTTONS.value,
    )

    filtered = utilities.filter(mock_assets + [widget_asset])

    assert widget_asset not in filtered
    assert len(filtered) == len(mock_assets)


def test_filter_assets_by_instance(mock_assets):
    sprites = utilities.filter(
        mock_assets,
        {Filters.INSTANCE.value: "sprites"},
    )
    assert len(sprites) == 1
    assert all(a.instance == AssetInstances.SPRITES.value for a in sprites)

    multi = utilities.filter(
        mock_assets,
        {Filters.INSTANCE.value: "sprites,crate.*"},
    )
    assert len(multi) == 2
    assert {a.instance for a in multi} == {
        AssetInstances.SPRITES.value,
        AssetInstances.CRATES.value,
    }


def test_filter_assets_by_category(mock_assets):
    sheets = utilities.filter(
        mock_assets,
        {Filters.CATEGORY.value: "sheets"},
    )
    assert len(sheets) == 3
    assert all(a.category == AssetCategories.SHEETS.value for a in sheets)


def test_filter_assets_by_id_and_name(mock_assets):
    jasilynn = utilities.filter(
        mock_assets,
        {Filters.ID.value: "jasilynn"},
    )
    assert len(jasilynn) == 1
    assert jasilynn[0].id == "jasilynn"

    obstacles = utilities.filter(
        mock_assets,
        {Filters.NAME.value: "test-obstacle-.*"},
    )
    assert len(obstacles) == 2
    assert all(a.name.startswith("test-obstacle-") for a in obstacles)


def test_filter_assets_conjunction(mock_assets):
    matched = utilities.filter(
        mock_assets,
        {
            Filters.CATEGORY.value: "sheets",
            Filters.INSTANCE.value: "players",
        },
    )
    assert len(matched) == 1
    assert matched[0].instance == AssetInstances.PLAYERS.value


def test_filter_assets_no_match(mock_assets):
    result = utilities.filter(
        mock_assets,
        {Filters.ID.value: "non_existent_key_12345"},
    )
    assert result == []


# ---------------------------------------------------------------------------
# ----------------------------------------------------------- UTILITIES: DUMP
# ---------------------------------------------------------------------------


def test_dump_state_success(mock_board, testbed, monkeypatch, tmp_path: Path):
    monkeypatch.setattr("app.static.settings.DUMP_DIR", tmp_path)

    utilities.dump(testbed, mock_board, Dumps.STATE.value)

    dumps = list(tmp_path.glob("*.state-dump.md"))
    assert len(dumps) == 1
    content = dumps[0].read_text(encoding="utf-8")
    assert "test-player" in content
    assert "test-crate" in content


def test_dump_state_with_filters(mock_board, testbed, monkeypatch, tmp_path: Path):
    monkeypatch.setattr("app.static.settings.DUMP_DIR", tmp_path)

    utilities.dump(
        testbed,
        mock_board,
        Dumps.STATE.value,
        filters={Filters.ID.value: "jasilynn"},
    )

    dumps = list(tmp_path.glob("*.state-dump.md"))
    assert len(dumps) == 1
    content = dumps[0].read_text(encoding="utf-8")
    assert "jasilynn" in content
    assert "test-crate" not in content


def test_dump_menus_success(mock_board, testbed, monkeypatch, tmp_path: Path):
    monkeypatch.setattr("app.static.settings.DUMP_DIR", tmp_path)

    utilities.dump(testbed, mock_board, Dumps.MENUS.value)

    dumps = list(tmp_path.glob("*.menus-dump.md"))
    assert len(dumps) == 1


def test_dump_sdl_success(mock_board, mock_registry, testbed, monkeypatch, tmp_path: Path):
    monkeypatch.setattr("app.static.settings.DUMP_DIR", tmp_path)

    utilities.dump(testbed, mock_board, Dumps.SDL.value)

    dumps = list(tmp_path.glob("*.sdl-dump.md"))
    assert len(dumps) == 1


def test_dump_registry_success(mock_engine, testbed, monkeypatch, tmp_path: Path):
    monkeypatch.setattr("app.static.settings.DUMP_DIR", tmp_path)

    utilities.dump(testbed, mock_engine, Dumps.REGISTRY.value)

    dumps = list(tmp_path.glob("*.registry-dump.md"))
    assert len(dumps) == 1


def test_dump_missing_template(mock_board, testbed, monkeypatch, tmp_path: Path, caplog):
    monkeypatch.setattr("app.static.settings.TEMPLATE_DIR", tmp_path / "missing_templates")
    monkeypatch.setattr("app.static.settings.DUMP_DIR", tmp_path)

    with caplog.at_level(logging.ERROR):
        utilities.dump(testbed, mock_board, Dumps.STATE.value)

    assert "Dump template not found" in caplog.text
    assert list(tmp_path.glob("*.md")) == []


# ---------------------------------------------------------------------------
# ---------------------------------------------- UTILITIES: HYDRATE & SCHEMA
# ---------------------------------------------------------------------------


def test_force_hydration(mock_engine, mock_migrator, testbed, monkeypatch):
    mock_engine.board.clear()
    mock_engine.board.loaded = False
    monkeypatch.setattr(mock_engine.registry, "prewarm", lambda budget_ms=99999: True)

    screensize = Dimensions(w=480, l=480)
    utilities.hydrate(mock_engine, testbed, screensize)

    assert mock_engine.board.loaded is True
    assert len(mock_engine.board.assets()) > 0
    assert "0" in mock_engine.screens


def test_serialize_schema_formats():
    yaml_out = utilities.serialize(StateSchema, "yaml")
    json_out = utilities.serialize(StateSchema, "json")

    parsed_yaml = yaml.safe_load(yaml_out)
    parsed_json = json.loads(json_out)

    assert isinstance(parsed_yaml, dict)
    assert parsed_yaml == parsed_json
    assert "properties" in parsed_json or "$defs" in parsed_json


# ---------------------------------------------------------------------------
# ----------------------------------------------------------------- HANDLERS
# ---------------------------------------------------------------------------


def test_handle_prerender_success(
    mock_engine,
    mock_orchestrator,
    mock_render,
    testbed,
    monkeypatch,
    tmp_path: Path,
):
    monkeypatch.setattr(mock_orchestrator, "orchestrate", lambda **kwargs: mock_engine)
    monkeypatch.setattr(utilities, "hydrate", lambda eng, brd, sz: None)

    args = argparse.Namespace(
        board=testbed,
        layer="0",
        out=str(tmp_path),
        device=Devices.KEYBOARD.value,
    )
    screensize = Dimensions(w=320, l=240)

    engine = handlers.handle_prerender(args, mock_orchestrator, screensize)

    expected_path = str(tmp_path / f"{testbed}-0-background.png")
    assert engine is mock_engine
    mock_render.save.assert_called_once_with(
        expected_path,
        mock_engine.screens["0"].boardsize.w,
        mock_engine.screens["0"].boardsize.l,
        target=mock_engine.screens["0"].bg_canvas,
    )


def test_handle_render_success(
    mock_engine,
    mock_orchestrator,
    mock_render,
    testbed,
    monkeypatch,
    tmp_path: Path,
):
    monkeypatch.setattr(mock_orchestrator, "orchestrate", lambda **kwargs: mock_engine)
    monkeypatch.setattr(utilities, "hydrate", lambda eng, brd, sz: None)

    args = argparse.Namespace(
        board=testbed,
        layer="0",
        out=str(tmp_path),
        device=Devices.KEYBOARD.value,
    )
    screensize = Dimensions(w=320, l=240)

    engine = handlers.handle_render(args, mock_orchestrator, screensize)

    expected_path = str(tmp_path / f"{testbed}-0.png")
    assert engine is mock_engine
    assert mock_render.render.called
    mock_render.save.assert_called_once_with(
        expected_path,
        mock_engine.screens["0"].screensize.w,
        mock_engine.screens["0"].screensize.l,
    )


def test_handle_render_full_success(
    mock_engine,
    mock_orchestrator,
    mock_render,
    testbed,
    monkeypatch,
    tmp_path: Path,
):
    monkeypatch.setattr(mock_orchestrator, "orchestrate", lambda **kwargs: mock_engine)
    monkeypatch.setattr(utilities, "hydrate", lambda eng, brd, sz: None)

    args = argparse.Namespace(
        board=testbed,
        layer="0",
        out=str(tmp_path),
        device=Devices.KEYBOARD.value,
    )
    screensize = Dimensions(w=320, l=240)

    engine = handlers.handle_map(args, mock_orchestrator, screensize)

    expected_path = str(tmp_path / f"{testbed}-0-full.png")
    assert engine is mock_engine
    assert mock_render.save.called
    assert mock_render.save.call_args[0][0] == expected_path


def test_handle_render_missing_layer(
    mock_engine,
    mock_orchestrator,
    mock_render,
    testbed,
    monkeypatch,
    tmp_path: Path,
    caplog,
):
    monkeypatch.setattr(mock_orchestrator, "orchestrate", lambda **kwargs: mock_engine)
    monkeypatch.setattr(utilities, "hydrate", lambda eng, brd, sz: None)

    args = argparse.Namespace(
        board=testbed,
        layer="nonexistent_layer",
        out=str(tmp_path),
        device=Devices.KEYBOARD.value,
    )
    screensize = Dimensions(w=320, l=240)

    with caplog.at_level(logging.ERROR):
        handlers.handle_render(args, mock_orchestrator, screensize)

    assert "Layer 'nonexistent_layer' not found" in caplog.text
    mock_render.save.assert_not_called()


def test_handle_start_keyboard_interrupt(
    mock_engine,
    mock_orchestrator,
    testbed,
    monkeypatch,
    caplog,
):
    monkeypatch.setattr(mock_orchestrator, "orchestrate", lambda **kwargs: mock_engine)

    def _raise_interrupt(*args, **kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(mock_engine, "start", _raise_interrupt)

    args = argparse.Namespace(
        board=testbed,
        device=Devices.KEYBOARD.value,
    )
    screensize = Dimensions(w=320, l=240)

    with caplog.at_level(logging.INFO):
        engine = handlers.handle_start(args, mock_orchestrator, screensize)

    assert engine is mock_engine
    assert "Game engine loop interrupted by user." in caplog.text


def test_handle_tags_scans_docstrings(tmp_path: Path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text('"""\n@domain.system\n@workflow.cli\n"""\n', encoding="utf-8")
    (pkg / "module_a.py").write_text('"""\n@app.core\n@workflow.cli\n"""\n', encoding="utf-8")
    (pkg / "_ignored.py").write_text('"""\n@should.ignore\n"""\n', encoding="utf-8")

    venv_dir = tmp_path / ".venv"
    venv_dir.mkdir()
    (venv_dir / "lib.py").write_text('"""\n@venv.ignore\n"""\n', encoding="utf-8")

    args = argparse.Namespace(directory=str(tmp_path))
    tags = handlers.handle_tags(args)

    assert tags == ["app.core", "domain.system", "workflow.cli"]


def test_handle_tags_missing_directory(tmp_path: Path):
    args = argparse.Namespace(directory=str(tmp_path / "missing_dir"))
    assert handlers.handle_tags(args) == []


def test_handle_schema_stdout_and_files(tmp_path: Path, capsys):
    # 1. Single schema to stdout
    stdout_args = argparse.Namespace(target="state", format="json", out=None)
    handlers.handle_schema(stdout_args)
    captured = capsys.readouterr()
    assert json.loads(captured.out)

    # 2. Single schema to file
    single_file = tmp_path / "state_schema.yaml"
    file_args = argparse.Namespace(target="state", format="yaml", out=str(single_file))
    handlers.handle_schema(file_args)
    assert single_file.exists()
    assert yaml.safe_load(single_file.read_text(encoding="utf-8"))

    # 3. All schemas to directory
    out_dir = tmp_path / "schemas"
    dir_args = argparse.Namespace(target="all", format="yaml", out=str(out_dir))
    handlers.handle_schema(dir_args)
    assert (out_dir / "schema-state.yaml").exists()
    assert (out_dir / "schema-properties.yaml").exists()
    assert (out_dir / "schema-configurations.yaml").exists()


# ---------------------------------------------------------------------------
# --------------------------------------------------------- MAIN ENTRYPOINT
# ---------------------------------------------------------------------------


def test_main_software_flag(mock_engine, testbed, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["main.py", "--software", "start", testbed])
    monkeypatch.delenv("SDL_RENDER_DRIVER", raising=False)
    monkeypatch.setitem(
        main.COMMAND_REGISTRY,
        Commands.START.value,
        lambda args, orch, sz: mock_engine,
    )
    monkeypatch.setattr(mock_engine, "stop", lambda: None)
    monkeypatch.setattr(main, "quit_sdl", lambda: None)

    main.commandline()

    assert os.environ.get("SDL_RENDER_DRIVER") == "software"


def test_main_dump_flags(mock_engine, testbed, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--dump-state",
            "--dump-menus",
            "--dump-sdl",
            "--dump-registry",
            "start",
            testbed,
        ],
    )
    monkeypatch.setitem(
        main.COMMAND_REGISTRY,
        Commands.START.value,
        lambda args, orch, sz: mock_engine,
    )
    monkeypatch.setattr(mock_engine, "stop", lambda: None)
    monkeypatch.setattr(main, "quit_sdl", lambda: None)

    dump_calls = []
    monkeypatch.setattr(
        utilities,
        "dump",
        lambda board, ctx, temp, filters=None: dump_calls.append((board, temp, filters)),
    )

    main.commandline()

    dumped_types = [call[1] for call in dump_calls]
    assert dumped_types == [
        Dumps.STATE.value,
        Dumps.MENUS.value,
        Dumps.SDL.value,
        Dumps.REGISTRY.value,
    ]


def test_main_dump_with_filter_flags(mock_engine, testbed, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "--dump-state",
            "--instance", "sprites",
            "--category", "sheets",
            "--id", "jasilynn",
            "--name", "test-sprite",
            "start",
            testbed,
        ],
    )
    monkeypatch.setitem(
        main.COMMAND_REGISTRY,
        Commands.START.value,
        lambda args, orch, sz: mock_engine,
    )
    monkeypatch.setattr(mock_engine, "stop", lambda: None)
    monkeypatch.setattr(main, "quit_sdl", lambda: None)

    captured_filters = {}
    monkeypatch.setattr(
        utilities,
        "dump",
        lambda board, ctx, temp, filters=None: captured_filters.update(filters or {}),
    )

    main.commandline()

    assert captured_filters == {
        Filters.INSTANCE.value: "sprites",
        Filters.CATEGORY.value: "sheets",
        Filters.ID.value: "jasilynn",
        Filters.NAME.value: "test-sprite",
    }


def test_main_standalone_command(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(sys, "argv", ["main.py", "tags", str(tmp_path)])

    quit_called = False

    def _quit():
        nonlocal quit_called
        quit_called = True

    monkeypatch.setattr(main, "quit_sdl", _quit)

    main.commandline()

    assert quit_called is False


def test_main_unknown_command(monkeypatch, caplog):
    monkeypatch.setattr(
        arguments,
        "construct",
        lambda root: argparse.Namespace(command="unknown_cmd", log_level="INFO"),
    )

    with caplog.at_level(logging.ERROR):
        with pytest.raises(SystemExit) as exc_info:
            main.commandline()

    assert exc_info.value.code == 1
    assert "Unknown Command: unknown_cmd" in caplog.text