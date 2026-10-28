"""
@domain.user
@app.devices
@app.semantics

# Ontology: Source - app.static.semantics.devices

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
    