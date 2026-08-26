"""
# Ontology: app.game.menus
"""
# Standard Libraries
from typing import List

# Application Libraries
from app.assets.base import Asset
from app.models.state import MenuState
from app.game.menus.controllers.base import MenuController

class Menu:
    id: str
    state: MenuState
    widgets: List[Asset]
    controller: MenuController