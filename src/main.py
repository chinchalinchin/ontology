"""
@workflow.cli
@workflow.entrypoints

# Ontology: cli

Package for command line interface.
"""
# Standard Libraries
import sys
import logging
import gc
import os
import faulthandler
from pathlib import Path


# ---------------------------------------------------------
# PATH RESOLUTION: Add project root to sys.path
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# CLI Libraries
import cli.handlers as handlers
import cli.arguments as arguments
import cli.utilities as utilities
from cli.enums import (
    Commands,
    EngineCommands,
    Dumps,
    Filters
)
# Application Libraries
from app.static.logging import configure_logging
from app.services.orchestration import Orchestrator

# Cython Libraries
from libs.core.models import Dimensions
from libs.graphics.render import quit_sdl

logger = logging.getLogger(__name__)

# ------------------------------------------------------

COMMAND_REGISTRY = {
    Commands.PRERENDER.value: handlers.handle_prerender,
    Commands.RENDER.value: handlers.handle_render,
    Commands.MAP.value: handlers.handle_map,
    Commands.START.value: handlers.handle_start,
    Commands.TELEMETRY.value: handlers.handle_telemetry,
    Commands.SCHEMA.value: handlers.handle_schema,
    Commands.TAGS.value: handlers.handle_tags
}

# ------------------------------------------------------

def commandline():
    faulthandler.enable()

    args = arguments.construct(PROJECT_ROOT)

    configure_logging(log_level=args.log_level.upper())

    logger.info("Command Line: %s", sys.argv[1:])

    handler = COMMAND_REGISTRY.get(args.command)
    if not handler:
        logger.error(f"Unknown Command: {args.command}")
        sys.exit(1)

    # ---------------------------------------------------------
    # STANDALONE EXECUTION (No SDL, no Orchestrator)
    # ---------------------------------------------------------
    if args.command not in EngineCommands:
        logger.info(f"Command: '{args.command}'")
        handler(args)
        logger.info("Application Completed.")
        return

    # ---------------------------------------------------------
    # ENGINE LIFECYCLE EXECUTION
    # ---------------------------------------------------------
    logger.info("EngineCommand: %s", args.command)

    screensize = Dimensions(w=args.width, l=args.length)

    if args.software:
        os.environ["SDL_RENDER_DRIVER"] = "software"

    orchestrator = Orchestrator()
    engine = handler(args, orchestrator, screensize)

    # Deferred Dumps Execution
    if args.dump_state:
        # State Query Filter Configuration
        state_filters = {
            "instance": args.instance,
            "category": args.category,
            "id": args.id,
            "name": args.name
        }
        utilities.dump(
            args.board, 
            engine.board, 
            Dumps.STATE.value, 
            filters=state_filters
        )

    if args.dump_menus:
        utilities.dump(
            args.board, 
            engine.board, 
            Dumps.MENUS.value
        )
        
    if args.dump_sdl:
        utilities.dump(
            args.board, 
            engine.board, 
            Dumps.SDL.value
        )
        
    if args.dump_registry:
        utilities.dump(
            args.board, 
            engine, 
            Dumps.REGISTRY.value
        )
    
    # Strictly ordered teardown to prevent post-SDL_Quit use-after-free
    if "engine" in locals() and engine is not None:
        engine.stop()
        del engine
        
    gc.collect()
    quit_sdl()
    logger.info("CLI processes completed.")

if __name__ == "__main__":
    commandline()