"""
@domain.logic
@app.device
@app.semantics

# Ontology: Source - app.static.semantics.devices

Enumeration of Device semanatics.
"""
# Standard Libraries
from enum import StrEnum

# ---------------------------------------

class Devices(StrEnum):
    CONTROLLER      = "controller"
    KEYBOARD        = "keyboard"

class DeviceContexts(StrEnum):
    WORLD           = "world"
    MENU            = "menu"
    