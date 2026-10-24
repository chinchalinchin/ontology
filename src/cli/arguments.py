"""
# Ontology: cli.arguments

Package for command line interface.
"""
# Standard Libraries
import argparse
import logging
from pathlib import Path

# Application Libraries
from app.static.semantics import Devices

# ------------------------------------------------------

logger = logging.getLogger(__name__)

SCREENSIZES = {
    'small': 360,
    'medium': 480,
    'large': 600
}
SCREENSIZE = SCREENSIZES['medium']

# ------------------------------------------------------

def construct(root: Path):
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
        p.add_argument("board", type=str)
        p.add_argument("--out", type=str, required=True)
        p.add_argument("--layer", type=str, required=True)
        p.add_argument("--width", type=int, default=SCREENSIZE)
        p.add_argument("--length", type=int, default=SCREENSIZE)
        p.add_argument("--device", type=str, default=Devices.KEYBOARD.value)

    # Interactive start subcommand: board_key is optional (nargs="?", default=None)
    p_start = subparsers.add_parser("start")
    p_start.add_argument("board", type=str, nargs="?", default=None,
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

    p_tags = subparsers.add_parser("tags", help="Export JSON or YAML model schemas.")
    p_tags.add_argument("directory", 
        type=str,
        nargs="?",
        default=root,
        metavar="DIR",
        help="Scan and list all @tags found in Python docstrings (default: script directory)."
    )
    return parser.parse_args()