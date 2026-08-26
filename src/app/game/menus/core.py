"""
# Ontology: app.models.menus

Models for typing the configuration attributes of Mechanics and other game components. See documentation for a more in-depth explanation of each field and its purpose. 
"""
# Standard Libraries
from dataclasses import dataclass
from typing import List

# Application Libraries
from app.assets.base import Asset
from app.models.state import MenuState

class Menu:
    id: str
    state: MenuState
    widgets: List[Asset]
    controller: 'MenuController'