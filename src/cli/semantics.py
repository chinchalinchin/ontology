"""
@domain.system
@app.semantics
@workflow.cli

# Ontology: Source - cli.semantics

Command Line semantics.
"""

from enum import StrEnum

class Commands(StrEnum):
    PRERENDER   = "prerender"
    RENDER      = "render"
    MAP         = "map"
    START       = "start"
    SCHEMA      = "schema"
    TAGS        = "tags"
    TELEMETRY   = "telemetry"

class EngineCommands(StrEnum):
    PRERENDER   = "prerender"
    RENDER      = "render"
    MAP         = "map"
    START       = "start"

class Dumps(StrEnum):
    STATE       = "state"
    MENUS       = "menus"
    REGISTRY    = "registry"
    SDL         = "sdl"

class Filters(StrEnum):
    INSTANCE    = "instance"
    CATEGORY    = "category"
    ID          = "id"
    NAME        = "name"