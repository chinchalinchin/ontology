"""
# Ontology: CLI
"""
import sys
import argparse
import logging
from pathlib import Path

# ---------------------------------------------------------
# PATH RESOLUTION: Add project root to sys.path
# This allows Python to find the /libs directory at the root
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config.enums import Devices
from app.hooks.orchestrator import Orchestrator
from libs.core import Dimensions
from libs.render import quit_sdl

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Ontology CLI Tools")
    # Added logging argument to the global CLI scope
    parser.add_argument("--log-level", type=str, default="INFO", 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], 
                        help="Set the application logging level.")
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Register common arguments across all subparsers
    for cmd in ["construct", "render"]:
        p = subparsers.add_parser(cmd)
        p.add_argument("board_key", type=str, help="The configuration key for the target board")
        p.add_argument("--out", type=str, required=True, help="Output directory path")
        p.add_argument("--layer", type=str, required=True, help="Target layer to construct/render")
        p.add_argument("--width", type=int, default=128, help="Simulated screen width")
        p.add_argument("--height", type=int, default=128, help="Simulated screen height")
        p.add_argument("--device", type=str, default=Devices.KEYBOARD, help="Player device")

    args = parser.parse_args()

    # Configure logging level dynamically based on args
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    logger.info(f"Starting CLI with command: '{args.command}' for board: '{args.board_key}'")

    # Step 1: Initialize Orchestrator and abstract components
    screensize = Dimensions(w=args.width, l=args.height)
    maestro = Orchestrator(args.board_key)
    
    # Device is None since we are headless and relying on static rendering
    logger.info("Orchestrating engine components for headless execution...")
    board, registry, screens = maestro.orchestrate(screensize, device=args.device)

    if args.layer not in screens:
        logger.error(f"Layer '{args.layer}' not found on board '{args.board_key}'.")
        quit_sdl()
        return

    screen = screens[args.layer]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Step 2: Route to encapsulated screen export methods
    if args.command == "construct":
        out_path = out_dir / f"{args.board_key}_{args.layer}_chunk.png"
        logger.info(f"Constructing background map image for layer '{args.layer}'...")
        screen.export_background(str(out_path))
        logger.info(f"Background successfully exported to: {out_path}")

    elif args.command == "render":
        out_path = out_dir / f"{args.board_key}_{args.layer}_render.png"
        assets = board.assets(args.layer)
        logger.info(f"Rendering composite frame for layer '{args.layer}'...")
        screen.export_render(str(out_path), assets, board.player, registry)
        logger.info(f"Composite frame successfully rendered and exported to: {out_path}")

    quit_sdl()
    logger.info("CLI processes completed.")

if __name__ == "__main__":
    main()