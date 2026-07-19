# Ontology: Pseudocode

## Package: ontology.app.interface

### Class: ontology.app.interface.controller.Controller

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
    board : Board 
    view : View
    pad : Controller

    def __init__(self, file : Path):
        # Initialize flags
        loaded = False
        paused = False

        # Initialize engine components
        self.pad = Controller()
        self.view = View()
        self.board = Board(file)
        
    def loop(self) -> None:
        while ingame and not self.paused:
            control = self.pad.poll()
            self.board.update(control)
            self.view.draw(board.pieces)
```

### ontology.app.world.view

TODO

```python
class View:

    def __init__(self):
        # TODO: initialize
        return

    def draw() -> None:
        return
```

### ontology.app.world.board

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