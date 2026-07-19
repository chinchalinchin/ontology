# Ontology: Pseudocode

## Package: ontology.app.interface

### Class: ontology.app.interface.player.Player

TODO

```
```

### Class: ontology.app.interface.player.Controller

TODO

```
```

## Package: ontology.app.world

### Class: ontology.app.world.engine.Engine

TODO

```python

class Engine:

    # Loop Mutators
    ingame : bool
    paused : bool 
    # Engine components
    board : Board 
    view : View
    player : Player

    def __init__(self, file : Path):
        # Initialize mutators
        loaded = False
        paused = False
        # Initialize engine components
        self.player = Player()
        self.view = View()
        self.board = Board(file)
        
    def loop(self) -> None:
        while ingame and not self.paused:
            # 1. Poll Player input
            control = self.player.poll()
            # 2. Update Board based on input
            self.board.update(control)
            # 3. Gather up Pieces
            pieces = self.board.pieces
            # 4. Draw Pieces on Board
            self.view.draw(pieces)
```

### ontology.app.world.view

TODO

```python
class View:

    # TODO: determine what datatype to use
    canvas : "?"

    def __init__(self):
        return

    def __render(self):
        # internal method for render
    
    def draw_sheet(self, sheets : List[Sheet]) -> None:
        for sheet in sheets:
            position, dimensions, frame = piece.get()
            canvas.render(position, dimensions, frame)
        return
```

### ontology.app.world.board.Board

TODO

```python
```

## ontology.app.registry

### ontology.app.registry.frames

Internal registry for frames.

```python
```

### ontology.app.registry.pipeline

Internal registry for compositions. Ingests asset configuration and assembles compositions.