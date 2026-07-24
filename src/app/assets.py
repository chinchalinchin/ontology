"""
Package for Asset classes.
"""
# Standard Libraries
from abc import ABC, abstractmethod
# Application Libraries
import app.models.state as state
import app.models.properties as properties

# -----------------------------------------------------------------------
# ------------------------------------------------------ FOUNDATION LEVEL
# -----------------------------------------------------------------------

class Asset(ABC):
    """
    Foundational class for all game Assets.
    """

    properties: properties.AssetProperties

    def __init__(self, properties.AssetProperties):
        self.properties = properties

    @abstractmethod
    def update(self) -> None:
        pass

# ------------------------------------------------------------------------
# ------------------------------------------------------ INTERMEDIATE LEVEL
# ------------------------------------------------------------------------

class Cursor(Asset):
    """
    """
    pass

class Effect(Asset):
    """
    """
    pass

class Menu(Asset):
    """
    """
    pass

class Object(Asset):
    """
    """
    properties

class Sheet(Asset):
    """
    """
    pass

# -------------------------------------------------------------------
# ------------------------------------------------------ ACTUAL LEVEL
# -------------------------------------------------------------------

# ------------------------------------------------------ TILES

class Tile(Asset):
    """
    Tile Asset class. Tiles are the simplest type of Asset, with property dimensions (asset, dimensions) and state dimensions (layer, position).
    """

    state: State.TileState
    
    def __init__(self, 
        properties: properties.AssetProperties,
        state: state.TileState
    ):
        super().__init__(properties)
        self.state = state

    def frame(self) -> str:
        return self.properties.asset

    def update(self, intent: State.Intention) -> None:
        return

# ------------------------------------------------------ OBJECTS

class Chest(Object):
    """
    """

    state: State.ChestState

    def __init__(self, 
        properties: properties.AssetProperties,
        state: state.ChestState
    ):
        super().__init__(properties)
        self.state = state
    
    def frame(self) -> str:
        return self.properties.asset + "-activated" if switch \
            else self.properties.asset + "-idle"

    def update(self, intent: State.Intention) -> None:
        # TODO: implement
        return

class Crate(Object):
    """
    """

    state: State.CrateState

    def __init__(self, 
        properties: properties.AssetProperties,
        state: state.CrateState
    ):
        super().__init__(properties)
        self.state = state
    
    def frame(self) -> str:
        return self.properties.asset

    def update(self, intent: State.Intention) -> None:
        # TODO: implement
        return

class Door(Object):
    """
    """

    state: State.DoorState

    def __init__(self, 
        properties: properties.AssetProperties,
        state: state.DoorState
    ):
        super().__init__(properties)
        self.state = state
    
    def frame(self) -> str:
        return self.properties.asset

    def update(self, intent: State.Intention) -> None:
        # TODO: implement
        return

class Gate(Object):
    """
    """

    state: State.GateState

    def __init__(self, 
        properties: properties.AssetProperties,
        state: state.GateState
    ):
        super().__init__(properties)
        self.state = state
    
    def frame(self) -> str:
        return self.properties.asset + "-activated" if switch \
            else self.properties.asset + "-idle"

    def update(self, intent: State.Intention) -> None:
        # TODO: implement
        return

class Plate(Object):
    """
    """

    state: State.PlateState

    def __init__(self, 
        properties: properties.AssetProperties,
        state: state.PlateState
    ):
        super().__init__(properties)
        self.state = state
    
    def frame(self) -> str:
        return self.properties.asset + "-activated" if switch \
            else self.properties.asset + "-idle"

    def update(self, intent: State.Intention) -> None:
        # TODO: implement
        return

# ------------------------------------------------------ CURSORS

class ExpressionCursor(Object):
    """
    """

    state: State.ExpressionCursorState

    def __init__(self, 
        properties: properties.AssetProperties,
        state: state.ExpressionCursorState
    ):
        super().__init__(properties)
        self.state = state
    
    def frame(self) -> str:
        return self.properties.asset

    def update(self, intent: State.Intention) -> None:
        # TODO: implement
        return

class ExpressionCursor(Object):
    """
    """

    state: State.ExpressionCursorState

    def __init__(self, 
        properties: properties.AssetProperties,
        state: state.ExpressionCursorState
    ):
        super().__init__(properties)
        self.state = state
    
    def frame(self) -> str:
        return self.properties.asset

    def update(self, intent: State.Intention) -> None:
        # TODO: implement
        return

class Projectile(Object):
    """
    """

    state: State.ProjectileState

    def __init__(self, 
        properties: properties.AssetProperties,
        state: state.ProjectileState
    ):
        super().__init__(properties)
        self.state = state
    
    def frame(self) -> str:
        return self.properties.asset

    def update(self, intent: State.Intention) -> None:
        # TODO: implement
        return

# ------------------------------------------------------ EFFECTS

# ------------------------------------------------------ SHEETS

# ------------------------------------------------------ MENU
