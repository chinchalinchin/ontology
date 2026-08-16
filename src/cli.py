"""
# Ontology: cli

Package for command line interface. Contains useful commands for debugging.
"""
# Standard Libraries
import sys
import argparse
import logging
from pathlib import Path
import datetime
import os

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
from app.hooks.orchestrator import Orchestrator

# Cython Libraries
from libs.core.models import Dimensions
from libs.graphics.render import quit_sdl, get_system_info

logger = logging.getLogger(__name__)

def dump(board_key, board, temp = 'state'):
    logger.info(f"Generating {temp} dump...")
    template_path = settings.TEMPLATE_DIR / settings.DUMP_TEMPLATES[temp]
    
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
        args['assets'] = board.assets()
    elif temp == 'sdl':
        args['sys_info'] = get_system_info()

    dump_str = template.render(**args)
    dump_out_path = Path.cwd() / f"{timestamp}.{temp}-dump.md"

    with open(dump_out_path, "w", encoding="utf-8") as f:
        f.write(dump_str)
        
    logger.info(f"State dump successfully written to {dump_out_path}")


def main():
    parser = argparse.ArgumentParser(description="Ontology CLI Tools")
    parser.add_argument("--log-level", type=str, default="INFO", 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], 
                        help="Set the application logging level.")
    parser.add_argument("--dump-state", action="store_true", default=False,
                        help="Generate a state dump markdown file after execution.")
    parser.add_argument("--dump-sdl", action="store_true", default=False,
                        help="Generate an SDL configuration dump markdown file after execution.")
    parser.add_argument("--software", action="store_true", default=False,
                        help="Force CPU software rendering (bypasses GPU).")

    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Register arguments for headless rendering subparsers
    for cmd in ["prerender", "render"]:
        p = subparsers.add_parser(cmd)
        p.add_argument("board_key", type=str, help="The configuration key for the target board")
        p.add_argument("--out", type=str, required=True, help="Output directory path")
        p.add_argument("--layer", type=str, required=True, help="Target layer to construct/render")
        p.add_argument("--width", type=int, default=300, help="Simulated screen width")
        p.add_argument("--height", type=int, default=300, help="Simulated screen height")
        p.add_argument("--device", type=str, default=Devices.KEYBOARD.value, help="Player device")

    # Register live game loop subparser
    p_start = subparsers.add_parser("start")
    p_start.add_argument("board_key", type=str, help="The configuration key for the target board")
    p_start.add_argument("--width", type=int, default=300, help="Window screen width")
    p_start.add_argument("--height", type=int, default=300, help="Window screen height")
    p_start.add_argument("--device", type=str, default=Devices.KEYBOARD.value, help="Player device")

    args = parser.parse_args()

    # Configure logging level dynamically based on args
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    logger.info(f"Starting CLI with command: '{args.command}' for board: '{args.board_key}'")

    # Step 1: Initialize Orchestrator and abstract components
    screensize = Dimensions(w=args.width, l=args.height)

    # Force the CPU renderer if requested prior to SDL Initialization
    if args.software:
        os.environ["SDL_RENDER_DRIVER"] = "software"
        logger.info("Forcing SDL to use CPU-bound software renderer via environment variable.")

    orchestrator = Orchestrator(args.board_key)
    
    if args.command in ["prerender", "render"]:
        # Headless static execution
        logger.info("Orchestrating engine components for headless execution...")
        board, registry, screens = orchestrator.init(screensize, device=args.device)

        if args.layer not in screens:
            logger.error(f"Layer '{args.layer}' not found on board '{args.board_key}'.")
            quit_sdl()
            return

        screen = screens[args.layer]
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)

        # Step 2: Route to encapsulated screen export methods
        if args.command == "prerender":
            out_path = out_dir / f"{args.board_key}-{args.layer}-background.png"
            logger.info(f"Constructing background map image for layer '{args.layer}'...")
            screen.export_background(str(out_path))
            logger.info(f"Background successfully exported to: {out_path}")

        elif args.command == "render":
            out_path = out_dir / f"{args.board_key}-{args.layer}.png"
            logger.info(f"Rendering composite frame for layer '{args.layer}'...")
            assets = board.renderables(args.layer)        
            player = board.player()

            screen.export_render(str(out_path), assets, player.state.position, player.dimensions)
            logger.info(f"Composite frame successfully rendered and exported to: {out_path}")
            
    elif args.command == "start":
        logger.info("Igniting engine for live execution...")
        engine = orchestrator.ignite(screensize, device=args.device)
        board = orchestrator.board
        
        if args.dump_sdl:
            dump(args.board_key, board, 'sdl')

        try:
            engine.start()
        except KeyboardInterrupt:
            logger.info("Game engine loop interrupted by user.")

    if args.dump_state:
        dump(args.board_key, board, 'state')
    
    # Cleanly release memory bounds
    del board
    del orchestrator

    quit_sdl()
    logger.info("CLI processes completed.")

if __name__ == "__main__":
    main()