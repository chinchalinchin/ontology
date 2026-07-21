# Ontology: Pseudocode

## Asset

```python
abstract class Asset:
    # Asset Identifier
    asset_key: str
    # Properties
    dimensions: Tuple[int, int]
    # State
    position: Tuple[int, int]
    frame_key: str
    layer_key: str

    abstract def update(self, intention: Intent) -> None:
        # Abstract method.
        # Updates current state based on input.
        # Recalculated frame_key. 
        
    def get(self) -> (Tuple[int, int], Tuple[int, int], str):
        return (self.position, self.dimensions, self.frame_key)
```

## Intent

```python
class Intent:
    # TODO
```

## Instruction

```python
class Instruction:
    # TODO
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
            control: Instruction  = self.player.poll()
            # 2. Update Board based on input
            self.player = self.board.play(control)
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
    Should be implemented in Cython (I think)

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
class Registry:

    assets = {
        "<asset-frame-key>": Image
    }

    def load(self):
        # parse /src/assets/ directory
        #
        # ```tree
        # ├── menu
        # │   └── main.yaml
        # ├── objects
        # │   ├── chests
        # │   ├── crates
        # │   ├── doors
        # │   ├── gates
        # │   ├── main.yaml
        # │   └── plates
        # ├── sheets
        # │   ├── main.yaml
        # │   ├── nymphs
        # │   ├── pixies
        # │   └── sprites
        # └── tiles
        #     ├── irregular
        #     ├── main.yaml
        #     └── regular
        # ```

```

## Board

```python
class Board:

    # Player
    player: Player
    # Tiles
    tiles: List[Asset]
    # Effects
    permanent: Dict[List[Asset]]
    temporary: Dict[List[Asset]]
    # Cursors
    expressions: Dict[List[Asset]]
    projectiles: Dict[List[Asset]]
    # Objects
    chests: Dict[List[Asset]]
    crates: Dict[List[Asset]]
    doors: Dict[List[Asset]]
    gates: Dict[List[Asset]]
    plates: Dict[List[Asset]]
    # Sheets
    pixies: Dict[List[Asset]]
    sprites: Dict[List[Asset]]

    def __init__(self, root: Path):
        # assume the folllowing directory structure for each board
        #
        # ```tree
        #    boards
        #    └── <board-key>
        #        └── immutable
        #            ├── animate.yaml
        #            └── inanimate.yaml
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
        for obj in self._objects():
            # perform object logic

        for sheet in self._sheets():
            # perform sheet logic
        
        # update player

```

## Sprite

```python
class Sprite(Asset):
    # Inherited Attributes
    ## Asset Identifier
    asset_key: str
    ## Properties
    dimensions: Tuple[int, int]
    ## State
    position: Tuple[int, int]
    layer_key: str
    frame_key: str

    # Unique Attributes
    ## Properties
    hitboxes: List[Tuple[int, int, int, int]]
    ## State
    direction: Direction # enum[UP, LEFT, DOWN, RIGHT]
    action: Action # enum[CAST, THRUST, WALK, SLASH, SHOOT, DIE]

    def update(self, intention: Intent) -> None:
        # Abstract implementation
        # Update state
```

## Player

```python
class Player(Asset):
    # Inherited Attributes
    ## Asset Identifier
    asset_key: str
    ## Properties
    dimensions: Tuple[int, int]
    ## State
    frame_key: str
    layer_key: str
    position: Tuple[int, int]

    # Unique Attributes
    ## Properties
    hitboxes: List[Tuple[int, int, int, int]]
    mappings: dict
    ## Extensions
    device: Controller | Keyboard

    def __init__(self, 
        device_type = Enum["controller" | "keyboard"]
    ):
        if device_type == "controller":
            self.device = Controller()
        else:
            self.device = Keyboard(mapping)

    def update(self, intention: Intent) -> None:
        # Abstract implementation
        # Update state

    def poll(self) -> Intent:
        intention = self.device.intend()
        # Map device to intent
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