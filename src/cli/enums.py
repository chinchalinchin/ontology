"""
@workflow.cli

# Ontology: cli.enums
"""

from enums import Enum

class Commands(str, Enum):
    PRERENDER   = "prerender"
    RENDER      = "render"
    MAP         = "map"
    START       = "start"
    SCHEMA      = "schema"
    TAGS        = "tags"
    TELEMETRY   = "telemetry"

class EngineCommands(str, Enum):
    PRERENDER   = "prerender"
    RENDER      = "render"
    MAP         = "map"
    START       = "start"

class Dumps(str, Enum):
    STATE       = "state"
    MENUS       = "menus"
    REGISTRY    = "registry"
    SDL         = "sdl"

class Filters(str, Enum):
    INSTANCES   = "instance"
    CATEGORIES  = "category"
    IDS         = "id"
    NAMES       = "name"