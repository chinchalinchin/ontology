"""
# Ontology: cli

Package for command line interface.
"""
# Standard Libraries
import sys
import argparse
import logging
import gc
import os
import datetime
from pathlib import Path

# External Libraries
import jinja2

# ---------------------------------------------------------
# PATH RESOLUTION: Add project root to sys.path
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Application Libraries
import app.config.settings as settings
from app.config.logging import configure_logging
from app.config.enums import Devices, AssetCategories
from app.game.screen import Screen
from app.services.orchestration.constructors import Orchestrator

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

# ---------------------------------------------------------
# COMMAND ARGUMENTS
# ---------------------------------------------------------

def arguments():
    parser = argparse.ArgumentParser(description="Ontology CLI Tools")
    parser.add_argument("--log-level", type=str, default="INFO", 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    parser.add_argument("--dump-state", action="store_true", default=False)
    parser.add_argument("--dump-menus", action="store_true", default=False)
    parser.add_argument("--dump-sdl", action="store_true", default=False)
    parser.add_argument("--dump-registry", action="store_true", default=False)
    parser.add_argument("--software", action="store_true", default=False)

    subparsers = parser.add_subparsers(dest="command", required=True)
    
    for cmd in ["prerender", "render", "map"]:
        p = subparsers.add_parser(cmd)
        p.add_argument("board_key", type=str)
        p.add_argument("--out", type=str, required=True)
        p.add_argument("--layer", type=str, required=True)
        p.add_argument("--width", type=int, default=SCREENSIZE)
        p.add_argument("--height", type=int, default=SCREENSIZE)
        p.add_argument("--device", type=str, default=Devices.KEYBOARD.value)

    p_start = subparsers.add_parser("start")
    p_start.add_argument("board_key", type=str)
    p_start.add_argument("--width", type=int, default=SCREENSIZE)
    p_start.add_argument("--height", type=int, default=SCREENSIZE)
    p_start.add_argument("--device", type=str, default=Devices.KEYBOARD.value)

    return parser.parse_args()

# ---------------------------------------------------------
# COMMAND HELPERS
# ---------------------------------------------------------

def dump(board_key, context, temp='state'):
    logger.info(f"Generating {temp} dump...")
    
    template_filename = getattr(settings, 'DUMP_TEMPLATES', {}).get(temp, f"{temp}.md")
    template_path = settings.TEMPLATE_DIR / template_filename
    
    if not template_path.exists():
        logger.error(f"Dump template not found at {template_path}")
        return
    
    with open(template_path, "r", encoding="utf-8") as f:
        template_str = f.read()
    
    template = jinja2.Template(template_str)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    args = {
        'board_key': board_key,
        'timestamp': timestamp
    }

    if temp == 'state':
        args['assets'] = context.assets()
        if hasattr(context, 'perimeters'):
            args['perimeters'] = context.perimeters() if callable(context.perimeters) else context.perimeters

    elif temp == 'menus':
        args['menus'] = context.menus
        args['overlays'] = context.overlays
        
    elif temp == 'sdl':
        args['sys_info'] = get_system_info()
        
    elif temp == 'registry':
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
            
        args['textures'] = list(screen.registry._textures.keys())
        args['frames'] = frames

    dump_str = template.render(**args)
    dump_out_path = Path.cwd() / f"{timestamp}.{temp}-dump.md"

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
            screen.rebake(tiles, size, screensize)
            engine.screens[layer] = screen
        else:
            engine.screens[layer] = Screen(screensize, size, tiles, registry)
            
    engine.board.loaded = True

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

    # Provide fallback focus if the board lacks a player
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
    
    try:
        engine.start()
    except KeyboardInterrupt:
        logger.info("Game engine loop interrupted by user.")
        
    return engine


# Dispatcher Registry
COMMAND_REGISTRY = {
    "prerender": handle_prerender,
    "render": handle_render,
    'map': handle_map,
    "start": handle_start
}

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    args = arguments()
    configure_logging(log_level=args.log_level.upper())

    logger.info(f"Starting CLI with command: '{args.command}' for board: '{args.board_key}'")

    screensize = Dimensions(w=args.width, l=args.height)

    if args.software:
        os.environ["SDL_RENDER_DRIVER"] = "software"

    orchestrator = Orchestrator()
    
    handler = COMMAND_REGISTRY.get(args.command)
    if not handler:
        logger.error(f"Unknown command received: {args.command}")
        sys.exit(1)

    engine = handler(args, orchestrator, screensize)

    # Deferred Dumps Execution
    if args.dump_state:
        dump(args.board_key, engine.board, 'state')

    if args.dump_menus:
        dump(args.board_key, engine.board, 'menus')
        
    if args.dump_sdl:
        dump(args.board_key, engine.board, 'sdl')
        
    if args.dump_registry:
        dump(args.board_key, engine, 'registry')
    
    if 'engine' in locals():
        del engine
        
    gc.collect()
    quit_sdl()
    logger.info("CLI processes completed.")
    
if __name__ == "__main__":
    main()