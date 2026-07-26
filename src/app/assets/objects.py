"""
Package for Object Assets.
"""
# Application Libraries
import app.assets as assets
import app.models.properties as properties
import app.models.state as state

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