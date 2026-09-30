"""
# Ontology: app.config.enums.devices

Device key enumeartions.
"""
# Standard Libraries
from enum import Enum

# -------------------------------- DEVICE ENUMERATIONS

class Devices(str, Enum):
    CONTROLLER      = "controller"
    KEYBOARD        = "keyboard"

class DeviceContexts(str, Enum):
    WORLD           = "world"
    MENU            = "menu"
    