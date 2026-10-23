"""
# Ontology: cli

Package for command line interface.
"""
# Standard Libraries
import sys
import argparse
import logging
import gc
import json
import os
import socket
import signal
import faulthandler
import datetime
import re
from pathlib import Path
from typing import Dict, List, Optional, Any

# External Libraries
import jinja2
import yaml
from pydantic import TypeAdapter

# ---------------------------------------------------------
# PATH RESOLUTION: Add project root to sys.path
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Application Libraries
import app.config.settings as settings
from app.config.logging import configure_logging
from app.config.enums import (
    Devices, 
    AssetCategories
)

from app.game.screen import Screen
from app.models.state import StateSchema
from app.models.properties import PropertiesSchema
from app.models.config import ConfigurationSchema
from app.services.orchestration import Orchestrator

# Cython Libraries
from libs.core.models import Dimensions, Position
from libs.graphics.render import quit_sdl, get_system_info

logger = logging.getLogger(__name__)

SCREENSIZES = {
    'small': 360,
    'medium': 480,
    'large': 600
}
SCREENSIZE = SCREENSIZES['medium']

SCHEMA_TARGETS = {
    "state": StateSchema,
    "properties": PropertiesSchema,
    "config": ConfigurationSchema,
}

# ---------------------------------------------------------
# COMMAND ARGUMENTS
# ---------------------------------------------------------

def arguments():
    parser = argparse.ArgumentParser(description="Ontology CLI Tools")
    parser.add_argument("--log-level", type=str, default="INFO", 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    parser.add_argument("--dump-state", action="store_true", default=False,
                        help="Export state dump upon execution termination.")
    parser.add_argument("--dump-menus", action="store_true", default=False)
    parser.add_argument("--dump-sdl", action="store_true", default=False)
    parser.add_argument("--dump-registry", action="store_true", default=False)
    parser.add_argument("--software", action="store_true", default=False)

    # State Dump Filter Arguments (Regex enabled, comma-delimited)
    parser.add_argument("--instances", type=str, default=None,
                        help="Comma-separated regex patterns to filter asset instances (e.g. 'sprites,crate.*').")
    parser.add_argument("--categories", type=str, default=None,
                        help="Comma-separated regex patterns to filter asset categories (e.g. 'sheets,objects').")
    parser.add_argument("--ids", type=str, default=None,
                        help="Comma-separated regex patterns to filter asset IDs.")
    parser.add_argument("--names", type=str, default=None,
                        help="Comma-separated regex patterns to filter asset names.")

    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Headless subcommands: board_key remains strictly required
    for cmd in ["prerender", "render", "map"]:
        p = subparsers.add_parser(cmd)
        p.add_argument("board_key", type=str)
        p.add_argument("--out", type=str, required=True)
        p.add_argument("--layer", type=str, required=True)
        p.add_argument("--width", type=int, default=SCREENSIZE)
        p.add_argument("--length", type=int, default=SCREENSIZE)
        p.add_argument("--device", type=str, default=Devices.KEYBOARD.value)

    # Interactive start subcommand: board_key is optional (nargs="?", default=None)
    p_start = subparsers.add_parser("start")
    p_start.add_argument("board_key", type=str, nargs="?", default=None,
                         help="Optional board key to bypass the Main Menu and start immediately.")
    p_start.add_argument("--width", type=int, default=SCREENSIZE)
    p_start.add_argument("--length", type=int, default=SCREENSIZE)
    p_start.add_argument("--device", type=str, default=Devices.KEYBOARD.value)

    # Schema Dump subcommand (Headless, no board_key required)
    p_schema = subparsers.add_parser("schema", help="Export JSON or YAML model schemas.")
    p_schema.add_argument(
        "--target",
        type=str,
        default="all",
        choices=["all", "state", "properties", "config"],
        help="Target model schema to export (default: 'all')."
    )
    p_schema.add_argument(
        "--format",
        type=str,
        default="yaml",
        choices=["json", "yaml"],
        help="Output serialization format (default: 'yaml')."
    )
    p_schema.add_argument(
        "--out",
        type=str,
        default=None,
        help="Output destination path or directory. Writes to stdout if omitted."
    )
    return parser.parse_args()

# ---------------------------------------------------------
# COMMAND HELPERS
# ---------------------------------------------------------

def filter(assets: List[Any], filters: Optional[Dict[str, Optional[str]]] = None) -> List[Any]:
    """
    Applies regex filtering to the Asset sequence across instances, categories, ids, and names.
    Excludes Widgets unconditionally.
    """
    # 1. Filter out Widgets
    non_widgets = [
        a for a in assets 
        if a.category != AssetCategories.WIDGETS.value
    ]
    if not filters:
        return non_widgets

    # 2. Compile active regex pattern sequences
    active_filters: Dict[str, List[re.Pattern]] = {}
    attr_map = {
        "instances": "instance",
        "categories": "category",
        "ids": "id",
        "names": "name",
    }

    for filter_key, attr_name in attr_map.items():
        raw_val = filters.get(filter_key)
        if raw_val:
            patterns = [p.strip() for p in raw_val.split(",") if p.strip()]
            active_filters[attr_name] = [re.compile(p) for p in patterns]

    if not active_filters:
        return non_widgets

    # 3. Predicate evaluation (conjunction of filters, disjunction of patterns per filter)
    matched_assets = []
    for asset in non_widgets:
        include = True
        for attr_name, compiled_list in active_filters.items():
            val = getattr(asset, attr_name, "") or ""
            if not any(regex.search(str(val)) for regex in compiled_list):
                include = False
                break
        if include:
            matched_assets.append(asset)

    return matched_assets


def dump(board_key: Optional[str], context: Any, temp: str = "state", filters: Optional[Dict[str, Optional[str]]] = None):
    logger.info(f"Generating {temp} dump...")
    
    template_filename = getattr(settings, "DUMP_TEMPLATES", {}).get(temp, f"{temp}.md")
    template_path = settings.TEMPLATE_DIR / template_filename
    
    if not template_path.exists():
        logger.error(f"Dump template not found at {template_path}")
        return
    
    with open(template_path, "r", encoding="utf-8") as f:
        template_str = f.read()
    
    template = jinja2.Template(template_str)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    args: Dict[str, Any] = {
        "board_key": board_key or "default",
        "timestamp": timestamp
    }

    if temp == "state":
        raw_assets = context.assets() if hasattr(context, "assets") else []
        args["assets"] = filter(raw_assets, filters)
        if hasattr(context, "perimeters"):
            args["perimeters"] = context.perimeters() if callable(context.perimeters) else context.perimeters
        if hasattr(context, "calendar"):
            args["calendar"] = context.calendar
        if hasattr(context, "plot"):
            args["plot"] = context.plot

    elif temp == "menus":
        args["menus"] = context.menus
        args["overlays"] = context.overlays
        
    elif temp == "sdl":
        args["sys_info"] = get_system_info()
        
    elif temp == "registry":
        screen = next(iter(context.screens.values()))
        
        frames = {}
        for k, v in screen.registry._frames.items():
            item_id, cx, cy, cw, cl = v
            frames[k] = {
                "item_id": item_id,
                "crop_x": cx,
                "crop_y": cy,
                "crop_w": cw,
                "crop_l": cl
            }
            
        args["textures"] = list(screen.registry._textures.keys())
        args["frames"] = frames

    dump_str = template.render(**args)
    dump_out_path = settings.DUMP_DIR / f"{timestamp}.{temp}-dump.md"

    with open(dump_out_path, "w", encoding="utf-8") as f:
        f.write(dump_str)
        
    logger.info(f"{temp.capitalize()} dump successfully written to {dump_out_path}")


def hydrate(engine, board_key, screensize):
    """
    Forces synchronous evaluation of the Migrator and Registry prewarming 
    for headless execution, then reallocates the VRAM canvases.
    """
    logger.info("Forcing synchronous state hydration for headless CLI...")
    
    # 1. Force Migrator to evaluate all state objects
    if engine.board.migrator:
        engine.board.migrator.target = board_key
        while not engine.board.migrator.step(budget_ms=99999):
            pass
            
    # 2. Force Registry to prewarm textures
    registry = next(iter(engine.screens.values())).registry
    if registry:
        while not registry.prewarm(budget_ms=99999):
            pass

    # 3. Rebake Screen canvases for the newly hydrated tiles
    old_screens = list(engine.screens.values())
    engine.screens.clear()
    
    for i, layer in enumerate(engine.board.layers()):
        tiles = engine.board.categories(AssetCategories.TILES.value, layer)
        layer_sizes = engine.board.size(layer)
        size = layer_sizes[0] if layer_sizes else screensize
        
        if i < len(old_screens):
            screen = old_screens[i]
            screen.rebake(tiles, size, engine.board.calendar, screensize)
            engine.screens[layer] = screen
        else:
            engine.screens[layer] = Screen(
                screensize, 
                size, 
                tiles, 
                registry, 
                engine.board.calendar
            )
            
    engine.board.loaded = True


def serialize(schema_cls: Any, fmt: str) -> str:
    """Generates and serializes a JSON Schema dictionary into JSON or YAML."""
    schema_dict = TypeAdapter(schema_cls).json_schema()
    if fmt == "yaml":
        return yaml.safe_dump(schema_dict, sort_keys=False, default_flow_style=False)
    return json.dumps(schema_dict, indent=2)

# ---------------------------------------------------------
# COMMAND HANDLERS
# ---------------------------------------------------------

def handle_map(args, orchestrator, screensize):
    logger.info("Orchestrating engine components for full board execution (render-full)...")
    engine = orchestrator.orchestrate(
        state_key=args.board_key, 
        screensize=screensize, 
        device=args.device,
        headless=True
    )

    hydrate(engine, args.board_key, screensize)
    
    if args.layer not in engine.screens:
        logger.error(f"Layer '{args.layer}' not found on board '{args.board_key}'.")
        return engine

    screen = engine.screens[args.layer]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{args.board_key}-{args.layer}-full.png"
    assets = engine.board.renderables(args.layer)        
    screen.export_map(str(out_path), assets)

    return engine


def handle_render(args, orchestrator, screensize):
    logger.info("Orchestrating engine components for headless execution (render)...")
    engine = orchestrator.orchestrate(
        state_key=args.board_key, 
        screensize=screensize, 
        device=args.device,
        headless=True
    )

    hydrate(engine, args.board_key, screensize)
    
    if args.layer not in engine.screens:
        logger.error(f"Layer '{args.layer}' not found on board '{args.board_key}'.")
        return engine

    screen = engine.screens[args.layer]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{args.board_key}-{args.layer}.png"
    assets = engine.board.renderables(args.layer)        
    player = engine.board.player()

    if player:
        focus, fdim = player.state.position, player.dimensions
    else:
        focus, fdim = Position(x=0, y=0), Dimensions(w=0, l=0)

    screen.export_render(str(out_path), assets, focus, fdim)

    return engine


def handle_prerender(args, orchestrator, screensize):
    logger.info("Orchestrating engine components for headless execution (prerender)...")
    engine = orchestrator.orchestrate(
        state_key=args.board_key, 
        screensize=screensize, 
        device=args.device,
        headless=True
    )
    
    hydrate(engine, args.board_key, screensize)
    
    if args.layer not in engine.screens:
        logger.error(f"Layer '{args.layer}' not found on board '{args.board_key}'.")
        return engine

    screen = engine.screens[args.layer]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{args.board_key}-{args.layer}-background.png"
    screen.export_background(str(out_path))

    return engine


def handle_start(args, orchestrator, screensize):
    logger.info("Igniting engine for live execution...")
    engine = orchestrator.orchestrate(
        state_key=args.board_key, 
        screensize=screensize, 
        device=args.device,
        headless=False
    )
    
    def _sig_handler(signum, frame):
        logger.info(f"Signal {signum} received. Requesting graceful engine shutdown...")
        engine.running = False

    # Intercept POSIX interruption signals to prevent thread-level C memory corruption
    prev_sigint = signal.signal(signal.SIGINT, _sig_handler)
    prev_sigterm = signal.signal(signal.SIGTERM, _sig_handler)

    try:
        engine.start()
    except KeyboardInterrupt:
        logger.info("Game engine loop interrupted by user.")
    finally:
        signal.signal(signal.SIGINT, prev_sigint)
        signal.signal(signal.SIGTERM, prev_sigterm)
        
    return engine


def handle_telemetry(args):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client.connect("/tmp/ontology.sock")
    except FileNotFoundError:
        logger.error("Ontology instance is not currently running with telemetry enabled.")
        return

    payload = json.dumps({
        "query": "assets",
        "params": {
            "instances": args.instances,
            "categories": args.categories,
            "ids": args.ids,
            "names": args.names
        }
    }).encode("utf-8")

    client.sendall(payload)
    response = client.recv(65536)
    print(json.dumps(json.loads(response.decode("utf-8")), indent=2))
    client.close()


def handle_schema(args: argparse.Namespace) -> None:
    """
    Exports JSON Schema definitions for StateSchema, PropertiesSchema,
    and ConfigurationSchema without initializing engine subsystems or SDL.
    """
    selected_targets = (
        list(SCHEMA_TARGETS.keys()) if args.target == "all" else [args.target]
    )
    
    out_path = Path(args.out).expanduser() if args.out else None

    # Multi-schema directory export or single-file export
    if out_path and (len(selected_targets) > 1 or out_path.is_dir() or not out_path.suffix):
        out_path.mkdir(parents=True, exist_ok=True)
        for target_key in selected_targets:
            cls = SCHEMA_TARGETS[target_key]
            rendered = serialize(cls, args.format)
            dest = out_path / f"{target_key}.schema.{args.format}"
            dest.write_text(rendered, encoding="utf-8")
            logger.info(f"Wrote {target_key} schema to {dest}")
        return

    # Single-target output to file or stdout
    combined_outputs = []
    for target_key in selected_targets:
        cls = SCHEMA_TARGETS[target_key]
        rendered = serialize(cls, args.format)
        
        if out_path:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(rendered, encoding="utf-8")
            logger.info(f"Wrote {target_key} schema to {out_path}")
            return
        
        combined_outputs.append(rendered)

    print("\n---\n".join(combined_outputs))


COMMAND_REGISTRY = {
    "prerender": handle_prerender,
    "render": handle_render,
    "map": handle_map,
    "start": handle_start,
    "telemetry": handle_telemetry,
    "schema": handle_schema
}

ENGINE_COMMANDS = { "prerender", "render", "map", "start" }

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    faulthandler.enable()

    args = arguments()
    configure_logging(log_level=args.log_level.upper())

    logger.info("Raw argv: %s", sys.argv[1:])
    logger.info("Parsed arguments: %s", vars(args))

    handler = COMMAND_REGISTRY.get(args.command)
    if not handler:
        logger.error(f"Unknown command received: {args.command}")
        sys.exit(1)

    # ---------------------------------------------------------
    # STANDALONE EXECUTION (No SDL, no Orchestrator, no Dimensions)
    # ---------------------------------------------------------
    if args.command not in ENGINE_COMMANDS:
        logger.info(f"Executing standalone command: '{args.command}'")
        handler(args)
        logger.info("CLI processes completed.")
        return

    # ---------------------------------------------------------
    # ENGINE LIFECYCLE EXECUTION
    # ---------------------------------------------------------
    logger.info(f"Starting CLI with command: '{args.command}' for board: '{getattr(args, 'board_key', None)}'")

    screensize = Dimensions(w=args.width, l=args.height)

    if args.software:
        os.environ["SDL_RENDER_DRIVER"] = "software"

    orchestrator = Orchestrator()
    engine = handler(args, orchestrator, screensize)

    # State Query Filter Configuration
    state_filters = {
        "instances": args.instances,
        "categories": args.categories,
        "ids": args.ids,
        "names": args.names
    }

    # Deferred Dumps Execution
    if args.dump_state:
        dump(args.board_key, engine.board, "state", filters=state_filters)

    if args.dump_menus:
        dump(args.board_key, engine.board, "menus")
        
    if args.dump_sdl:
        dump(args.board_key, engine.board, "sdl")
        
    if args.dump_registry:
        dump(args.board_key, engine, "registry")
    
    # Strictly ordered teardown to prevent post-SDL_Quit use-after-free
    if "engine" in locals() and engine is not None:
        engine.stop()
        del engine
        
    gc.collect()
    quit_sdl()
    logger.info("CLI processes completed.")

if __name__ == "__main__":
    main()