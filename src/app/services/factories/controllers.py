"""
@domain.system
@app.service
@app.menu
@menu.controller
@workflow.injection

# Ontology: Source - app.services.factories.controllers

Factory for instantiating Menu Controllers.
"""
# Application Libraries
from app.game.menus.controllers import (
    MenuController,
    DisplayController,
    InventoryController,
    LoadController,
    MainController,
    OptionsController,
    PauseController,
    ScrollController
)
from app.static.semantics import Controllers


class ControllerFactory:
    """
    ## ControllerFactory

    Resolves MenuController implementations from declarative controller keys.
    """
    _CONTROLLERS = {
        Controllers.DISPLAY.value: DisplayController,
        Controllers.INVENTORY.value: InventoryController,
        Controllers.LOAD.value: LoadController,
        Controllers.MAIN.value: MainController,
        Controllers.OPTIONS.value: OptionsController,
        Controllers.PAUSE.value: PauseController,
        Controllers.SCROLL.value: ScrollController,
    }

    @classmethod
    def controller(cls, kind: str) -> MenuController:
        target_cls = cls._CONTROLLERS.get(kind, ScrollController)
        return target_cls()