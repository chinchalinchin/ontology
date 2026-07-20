# Ontology: API

# ontology.app.intent.Intent

Attributes
    - 

def () -> ()

# ontology.app.asset.Asset

Attributes
    - id: `int`
    - layer: `int`
    - dimensions: `tuple[w, h]`
    - position: `tuple[w, h]`
    - frame: `img`

def _frame(self) -> None:
    Abstract private method.
    Calculates current frame based on state.
    Updates frame.

def update(self, msg: Intent) -> None:
    Abstract public method.
    Updates current state based on input.
    
def get(self) -> (position, dimensions, frame):
    Public method.
    Returns (position, dimensions, self._frame())

# ontology.app.interface.player.Player

Attributes:
    - device: `enum[controller | keyboard]`

def poll() -> Intent
    Maps device Input State to Intent
    Returns Intent

# ontology.app.interface.player.Controller

def state() -> Input State

# ontology.app.interface.player.Keyboard

def state() -> Input State

