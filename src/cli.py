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
from app.config.enums import Devices
from app.services.constructors import Orchestrator

# Cython Libraries
from libs.core.models import Dimensions
from libs.graphics.render import quit_sdl, get_system_info

logger = logging.getLogger(__name__)

def dump(board_key, context, temp='state'):
    logger.info(f"Generating {temp} dump...")
    
    template_filename = getattr(settings, 'DUMP_TEMPLATES', {}).get(temp, f"{temp}.md")
    template_path = settings.TEMPLATE_DIR / template_filename
    
    if not template_path.exists():
        logger.error(f"State dump template not found at {template_path}")
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
        
    logger.info(f"State dump successfully written to {dump_out_path}")


def arguments():
    parser = argparse.ArgumentParser(description="Ontology CLI Tools")
    parser.add_argument("--log-level", type=str, default="INFO", 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    parser.add_argument("--dump-state", action="store_true", default=False)
    parser.add_argument("--dump-sdl", action="store_true", default=False)
    parser.add_argument("--dump-registry", action="store_true", default=False)
    parser.add_argument("--software", action="store_true", default=False)

    subparsers = parser.add_subparsers(dest="command", required=True)
    
    for cmd in ["prerender", "render"]:
        p = subparsers.add_parser(cmd)
        p.add_argument("board_key", type=str)
        p.add_argument("--out", type=str, required=True)
        p.add_argument("--layer", type=str, required=True)
        p.add_argument("--width", type=int, default=480)
        p.add_argument("--height", type=int, default=480)
        p.add_argument("--device", type=str, default=Devices.KEYBOARD.value)

    p_start = subparsers.add_parser("start")
    p_start.add_argument("board_key", type=str)
    p_start.add_argument("--width", type=int, default=480)
    p_start.add_argument("--height", type=int, default=480)
    p_start.add_argument("--device", type=str, default=Devices.KEYBOARD.value)

    return parser.parse_args()


# ---------------------------------------------------------
# COMMAND HANDLERS
# ---------------------------------------------------------

def handle_prerender(args, orchestrator, screensize):
    logger.info("Orchestrating engine components for headless execution (prerender)...")
    engine = orchestrator.orchestrate(
        state_key=args.board_key, 
        screensize=screensize, 
        device=args.device,
        headless=True
    )
    
    if args.layer not in engine.screens:
        logger.error(f"Layer '{args.layer}' not found on board '{args.board_key}'.")
        return engine

    screen = engine.screens[args.layer]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{args.board_key}-{args.layer}-background.png"
    screen.export_background(str(out_path))

    return engine


def handle_render(args, orchestrator, screensize):
    logger.info("Orchestrating engine components for headless execution (render)...")
    engine = orchestrator.orchestrate(
        state_key=args.board_key, 
        screensize=screensize, 
        device=args.device,
        headless=True
    )
    
    if args.layer not in engine.screens:
        logger.error(f"Layer '{args.layer}' not found on board '{args.board_key}'.")
        return engine

    screen = engine.screens[args.layer]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{args.board_key}-{args.layer}.png"
    
    assets = engine.board.renderables(args.layer)        
    player = engine.board.player()

    screen.export_render(str(out_path), assets, player.state.position, player.dimensions)

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
    "start": handle_start
}

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    args = arguments()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    logger.info(f"Starting CLI with command: '{args.command}' for board: '{args.board_key}'")

    screensize = Dimensions(w=args.width, l=args.height)

    if args.software:
        os.environ["SDL_RENDER_DRIVER"] = "software"

    orchestrator = Orchestrator()
    
    handler = COMMAND_REGISTRY.get(args.command)
    if not handler:
        logger.error(f"Unknown command received: {args.command}")
        sys.exit(1)

    # Execute designated function and capture the engine instance
    engine = handler(args, orchestrator, screensize)

    # Deferred Dumps Execution
    if args.dump_state:
        dump(args.board_key, engine.board, 'state')
        
    if args.dump_sdl:
        dump(args.board_key, engine.board, 'sdl')
        
    if args.dump_registry:
        dump(args.board_key, engine, 'registry')
    
    # Cleanly release memory bounds
    if 'engine' in locals():
        del engine
        
    gc.collect()
    quit_sdl()
    logger.info("CLI processes completed.")

if __name__ == "__main__":
    main()