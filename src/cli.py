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
# This allows Python to find the /libs directory at the root
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
    
    # Safely resolve template name, defaulting to <temp>.md if not registered in settings
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
        # Safely extract registry from the first available screen
        screen = next(iter(context.screens.values()))
        
        frames = {}
        for k, v in screen.registry._frames.items():
            tex_ptr, cx, cy, cw, cl = v
            frames[k] = {
                "tex_w": tex_ptr.w,
                "tex_l": tex_ptr.l,
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
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], 
                        help="Set the application logging level.")
    parser.add_argument("--dump-state", action="store_true", default=False,
                        help="Generate a state dump markdown file after execution.")
    parser.add_argument("--dump-sdl", action="store_true", default=False,
                        help="Generate an SDL configuration dump markdown file after execution.")
    parser.add_argument("--dump-registry", action="store_true", default=False,
                        help="Generate a Registry mapping dump markdown file after execution.")
    parser.add_argument("--software", action="store_true", default=False,
                        help="Force CPU software rendering (bypasses GPU).")

    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Register arguments for headless rendering subparsers
    for cmd in ["prerender", "render"]:
        p = subparsers.add_parser(cmd)
        p.add_argument("board_key", type=str, help="The configuration key for the target board")
        p.add_argument("--out", type=str, required=True, help="Output directory path")
        p.add_argument("--layer", type=str, required=True, help="Target layer to construct/render")
        p.add_argument("--width", type=int, default=360, help="Simulated screen width")
        p.add_argument("--height", type=int, default=360, help="Simulated screen height")
        p.add_argument("--device", type=str, default=Devices.KEYBOARD.value, help="Player device")

    # Register live game loop subparser
    p_start = subparsers.add_parser("start")
    p_start.add_argument("board_key", type=str, help="The configuration key for the target board")
    p_start.add_argument("--width", type=int, default=360, help="Window screen width")
    p_start.add_argument("--height", type=int, default=360, help="Window screen height")
    p_start.add_argument("--device", type=str, default=Devices.KEYBOARD.value, help="Player device")

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
        return engine.board

    screen = engine.screens[args.layer]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{args.board_key}-{args.layer}-background.png"
    logger.info(f"Constructing background map image for layer '{args.layer}'...")
    screen.export_background(str(out_path))
    logger.info(f"Background successfully exported to: {out_path}")

    return engine.board


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
        return engine.board

    screen = engine.screens[args.layer]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{args.board_key}-{args.layer}.png"
    logger.info(f"Rendering composite frame for layer '{args.layer}'...")
    
    assets = engine.board.renderables(args.layer)        
    player = engine.board.player()

    screen.export_render(str(out_path), assets, player.state.position, player.dimensions)
    logger.info(f"Composite frame successfully rendered and exported to: {out_path}")

    return engine.board


def handle_start(args, orchestrator, screensize):
    logger.info("Igniting engine for live execution...")
    engine = orchestrator.orchestrate(
        state_key=args.board_key, 
        screensize=screensize, 
        device=args.device,
        headless=False
    )
    
    if args.dump_sdl:
        dump(args.board_key, engine.board, 'sdl')
        
    if args.dump_registry:
        dump(args.board_key, engine, 'registry')

    try:
        engine.start()
    except KeyboardInterrupt:
        logger.info("Game engine loop interrupted by user.")
        
    return engine.board


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
    """
    ## main

    Command line entrypoint for the application.
    """
    args = arguments()

    # Configure logging level dynamically based on args
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    logger.info(f"Starting CLI with command: '{args.command}' for board: '{args.board_key}'")

    screensize = Dimensions(w=args.width, l=args.height)

    # Force the CPU renderer if requested prior to SDL Initialization
    if args.software:
        os.environ["SDL_RENDER_DRIVER"] = "software"
        logger.info("Forcing SDL to use CPU-bound software renderer via environment variable.")

    # Initialize Builder Pattern
    orchestrator = Orchestrator()
    
    # Dispatch execution based on parsed command
    handler = COMMAND_REGISTRY.get(args.command)
    if not handler:
        logger.error(f"Unknown command received: {args.command}")
        sys.exit(1)

    # Execute designated function and capture the board state for potential dumping
    board = handler(args, orchestrator, screensize)

    if args.dump_state and board:
        dump(args.board_key, board, 'state')
    
    # Cleanly release memory bounds
    if 'board' in locals():
        del board
        
    gc.collect()
    quit_sdl()
    logger.info("CLI processes completed.")

if __name__ == "__main__":
    main()