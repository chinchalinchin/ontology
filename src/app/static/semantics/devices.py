"""
@app.semantics
@app.input

# Ontology: Source - app.config.enums.devices

Enumeration of Device semanatics.
"""
# Standard Libraries
from enum import Enum

# ---------------------------------------

class Devices(str, Enum):
    CONTROLLER      = "controller"
    KEYBOARD        = "keyboard"

class DeviceContexts(str, Enum):
    WORLD           = "world"
    MENU            = "menu"
    