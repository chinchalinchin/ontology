"""
@domain.logic
@main.cli

# Ontology: cli

Package for command line interface.
"""
# Standard Libraries
import ast
import argparse
import logging
import json
import socket
import signal
from pathlib import Path

# CLI Libraries
import cli.utilities as utilities

# Application Libraries
from app.models.state import StateSchema
from app.models.properties import PropertiesSchema
from app.models.config import ConfigurationSchema

# Cython Libraries
from libs.core.models import (
    Dimensions, 
    Position
)

logger = logging.getLogger(__name__)

SCHEMA_TARGETS = {
    "state": StateSchema,
    "properties": PropertiesSchema,
    "configuration": ConfigurationSchema,
}

# ---------------------------------------------------------
# COMMAND HANDLERS
# ---------------------------------------------------------

def handle_tags(args) -> list[str]:
    """
    Scans a directory for Python files and returns an alphabetized list of
    all unique tags found in module docstrings.

    Args:
        directory: Directory path to scan. Defaults to the script directory.

    Returns:
        list[str]: Sorted list of unique tag names without the '@' prefix.
    """
    root = Path(args.directory).expanduser().resolve()

    if not root.exists() or not root.is_dir():
        print(f"Error: Directory not found at {root}")
        return []

    tags = set()

    for file_path in root.rglob("*.py"):
        if ".venv" in file_path.parts:
            continue
        
        if file_path.name.startswith((".", "_")) and file_path.name != "__init__.py":
            continue

        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue

        docstring = ast.get_docstring(tree)
        if not docstring:
            continue

        for token in docstring.split():
            if token.startswith("@") and len(token) > 1:
                cleaned = token.lstrip("@").rstrip(".,;:()")
                if cleaned:
                    tags.add(cleaned)

    sorted_tags = sorted(tags)
    logger.info(sorted_tags)
    return sorted_tags

def handle_map(args, orchestrator, screensize):
    logger.info("Orchestrating engine components for full board execution (render-full)...")
    engine = orchestrator.orchestrate(
        state_key=args.board, 
        screensize=screensize, 
        device=args.device,
        headless=True
    )

    utilities.hydrate(engine, args.board, screensize)
    
    if args.layer not in engine.screens:
        logger.error(f"Layer '{args.layer}' not found on board '{args.board}'.")
        return engine

    screen = engine.screens[args.layer]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{args.board}-{args.layer}-full.png"
    assets = engine.board.renderables(args.layer)        
    screen.export_map(str(out_path), assets)

    return engine


def handle_render(args, orchestrator, screensize):
    logger.info("Orchestrating engine components for headless execution (render)...")
    engine = orchestrator.orchestrate(
        state_key=args.board, 
        screensize=screensize, 
        device=args.device,
        headless=True
    )

    utilities.hydrate(engine, args.board, screensize)
    
    if args.layer not in engine.screens:
        logger.error(f"Layer '{args.layer}' not found on board '{args.board}'.")
        return engine

    screen = engine.screens[args.layer]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{args.board}-{args.layer}.png"
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
        state_key=args.board, 
        screensize=screensize, 
        device=args.device,
        headless=True
    )
    
    utilities.hydrate(engine, args.board, screensize)
    
    if args.layer not in engine.screens:
        logger.error(f"Layer '{args.layer}' not found on board '{args.board}'.")
        return engine

    screen = engine.screens[args.layer]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{args.board}-{args.layer}-background.png"
    screen.export_background(str(out_path))

    return engine


def handle_start(args, orchestrator, screensize):
    logger.info("Igniting engine for live execution...")
    engine = orchestrator.orchestrate(
        state_key=args.board, 
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
            rendered = utilities.serialize(cls, args.format)
            dest = out_path / f"schema-{target_key}.{args.format}"
            dest.write_text(rendered, encoding="utf-8")
            logger.info(f"Wrote {target_key} schema to {dest}")
        return

    # Single-target output to file or stdout
    combined_outputs = []
    for target_key in selected_targets:
        cls = SCHEMA_TARGETS[target_key]
        rendered = utilities.serialize(cls, args.format)
        
        if out_path:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(rendered, encoding="utf-8")
            logger.info(f"Wrote {target_key} schema to {out_path}")
            return
        
        combined_outputs.append(rendered)

    print("\n---\n".join(combined_outputs))