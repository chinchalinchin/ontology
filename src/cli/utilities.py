"""
@workflow.cli

# Ontology: cli.utilities

"""
# Standard Libraries
import json
import datetime
import re
import logging
from typing import (
    Dict, 
    List, 
    Optional, 
    Any
)
# External Libraries
import jinja2
import yaml
from pydantic import TypeAdapter

# CLI Libraries
from cli.enums import (
    Dumps,
    Filters
)
# Application Libraries
import app.config.settings as settings
from app.config.enums import AssetCategories
from app.game.screen import Screen

# Cython Libraries
from libs.graphics.render import sysinfo

logger = logging.getLogger(__name__)

# ------------------------------------------------------

def filter(
    assets: List[Any], 
    filters: Optional[Dict[str, Optional[str]]] = None
) -> List[Any]:
    """
    Applies regex filtering to the Asset sequence across instances, categories, ids, 
    and names. Excludes Widgets unconditionally.
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

    for filter_key, filter_name in Filters:
        raw_val = filters.get(filter_key)
        if raw_val:
            patterns = [p.strip() for p in raw_val.split(",") if p.strip()]
            active_filters[filter_name] = [re.compile(p) for p in patterns]

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


def dump(
    board: Optional[str], 
    context: Any, 
    temp: str, 
    filters: Optional[Dict[str, Optional[str]]] = None
):
    logger.info(f"Generating {temp} dump...")
    
    template_filename = settings.DUMP_TEMPLATES.get(temp, '.state-dump.md.j2')
    template_path = settings.TEMPLATE_DIR / template_filename
    
    if not template_path.exists():
        logger.error(f"Dump template not found at {template_path}")
        return
    
    with open(template_path, "r", encoding="utf-8") as f:
        template_str = f.read()
    
    template = jinja2.Template(template_str)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    args: Dict[str, Any] = {
        "board_key": board,
        "timestamp": timestamp
    }

    if temp == Dumps.STATE.value:
        raw_assets = context.assets() if hasattr(context, "assets") else []
        args["assets"] = filter(raw_assets, filters)
        if hasattr(context, "perimeters"):
            args["perimeters"] = context.perimeters() if callable(context.perimeters) else context.perimeters
        if hasattr(context, "calendar"):
            args["calendar"] = context.calendar
        if hasattr(context, "plot"):
            args["plot"] = context.plot

    elif temp == Dumps.MENUS.value:
        args["menus"] = context.menus
        args["overlays"] = context.overlays
        
    elif temp == Dumps.SDL.value:
        args["sys_info"] = sysinfo()
        
    elif temp == Dumps.REGISTRY.value:
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
