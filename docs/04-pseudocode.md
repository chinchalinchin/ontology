# Ontology: Pseudocode

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
            control = self.player.poll()
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

```python
class View:
    # Static image assembled from immutable assets
    canvas: "TODO: Data Type?"
    # Buffer to hold copy of canvas for rendering
    buffer: "TODO: Data Type?"
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
    ) -> "TODO: Data Type?":
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
    ) -> "TODO: Data Type?":
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
        #    └── world-00
        #        ├── immutable.yaml
        #        └── mutable
        #            ├── animate.yaml
        #            ├── inanimate.yaml
        #            └── player.yaml
        # ```
```
