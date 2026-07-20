# Ontology: Pseudocode

## Asset

```python
abstract class Asset:
    key: int
    layer: int
    dimensions: tuple[w, h]
    position: tuple[w, h]
    hitboxes: list[ tuple[x, y, w, h] ]
    frame: Image

    abstract def _frame(self) -> None:
        # Abstract private method.
        # Calculates current frame based on state.
        # Updates frame.

    abstract def update(self, msg: Intent) -> None:
        # Abstract public method.
        # Updates current state based on input.
        
    def get(self) -> (position, dimensions, frame):
        # Public method.
        return (position, dimensions, self._frame())
```

### Intent

```python
```

## Engine

```python
class Engine:
    # Loop Mutators
    ingame : bool
    paused : bool 
    # Engine components
    board : Board 
    view : View
    player : Player

    def __init__(self, file: Path, screen: Tuple[int, int]):
        # Initialize mutators
        loaded = False
        paused = False
        # Initialize engine components
        self.player = Player()
        self.board = Board(file)
        self.views = [
            View(screen, self.board.pieces.immutable[layer])
            for layer 
            in self.board.layers
        ]
        
    def loop(self) -> None:
        while ingame and not self.paused:
            # 1. Poll Player input
            control : Intent = self.player.poll()
            # 2. Update Board based on input
            self.board.update(control)
            # 3. Determine current layer
            layer = self.board.layer
            # 4. Gather up pieces
            pieces = self.board.pieces[layer].mutable
            # 5. Draw pieces on Board
            self.views[layer].draw(pieces)
            # ETC: calculate frame rates, lag, buffer rates, skips, etc. 
```

## View

!!! note
    Should be implemented in Cython

```python
class View:
    # Static image assembled from immutable assets
    canvas: Image
    # Buffer to hold copy of canvas for rendering
    buffer: Image
    # Screen size
    screen: Tuple[int, int]


    def __init__(self, 
        screen: Tuple[int, int], 
        immutable: List[Asset]
    ):
        self.screen = screen
        self.canvas(immutable)
        return

    def _onscreen(self, 
        pov: Tuple[int, int], 
        pos: Tuple[int, int], 
        dim: Tuple[int, int]
    ) -> bool:
        result = False
        # calculate result
        return result
    
    def canvas(self, 
        assets: List[Asset]
    ) -> Image:
        """
        Render and stack immutable assets onto static canvas.
        """
        for asset in assets:
            position, dimensions, frame = asset.get()
            self.canvas.render(position, dimensions, frame)

        return self.canvas

    def draw(self, 
        assets : List[Asset], 
        pov: Tuple[int, int]
    ) -> Image:
        """
        Render mutable assets onto the immutable canvas.
        """
        # 1. Copy static canvas into new buffer
        self.buffer = self.canvas.copy()

        # 2. Render all onscreen assets
        for asset in assets:
            position, dimensions, frame = asset.get()
            if self._onscreen(pov, position, dimensions):
                self.buffer.render(position, dimensions, frame)
        
        # 3. Clip bufer to the player's POV
        self.buffer.clip(pov)
        return self.buffer
```

## Registry

!!! note
    Should be implemented in Cython
    
```python
```

## Board

```python
class Board:

    # Player
    player: Player
    # Tiles
    tiles: List[Asset]
    # Objects
    chests: List[Asset]
    crates: List[Asset]
    doors: List[Asset]
    gates: List[Asset]
    plates: List[Asset]
    # Sheets
    nymphs: List[Asset]
    pixies: List[Asset]
    sprites: List[Asset]    

    def __init__(self, root: Path):
        # assume the folllowing directory structure for each board
        #
        # ```
        #    boards
        #    └── <board-key>
        #        ├── immutable.yaml
        #        └── mutable
        #            ├── animate.yaml
        #            └── inanimate.yaml
        # ```

    def _objects(self) -> List[Asset]:
        return self.chests + self.crates + self.doors + self.gates + self.plates

    def _sheets(self) -> List[Asset]:
        return self.nymphs + self.pixies + self.sprites

    def pieces(self) -> List[Asset]:
        return self.tiles + self._objects() + self._sheets()

    def update(self, intent: Intent) -> None:
        # game logic
```

## Player

```python
class Player:
    device: Controller | Keyboard
    mappings: dict

    def __init__(self, 
        device_type = Enum["controller" | "keyboard"]
    ):
        if device_type == "controller":
            self.device = Controller()
        else:
            self.device = Keyboard(mapping)

    def poll(self) -> Intent:
        intention = self.device.intend()
        return Intent(intention)
```

## Device

```python
abstract class Device:
    mapping: Mapping

    def __init__(self, 
        device_type = Enum["controller" | "keyboard"]
    ):
        self.mapping = Mapping(device_type)

    abstract def intend -> Intent
```

## Controller

```python
class Controller(Device):

    # Device Implementation
    def intend() -> Intent:
        # calculate controller state
        return state
```

## Keyboard

```python
class Keyboard(Device):

    # Device Implementation
    def intend() -> Intent:
        # calculate keyboard state
        return state
```