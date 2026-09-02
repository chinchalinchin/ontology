##### Refactor: Phase 05.06 - Event Bus Routing & Handlers

**Overview**

The `Engine._drain()` method currently utilizes a monolithic `if/elif isinstance` chain to process game events. As the engine scales to include dialogue, commerce, and editor events, this tightly couples menu and transition logic directly into the core game loop.

This phase refactors the Event Bus into a Strategy/Command pattern. By introducing an `EventContext` object and an `EventHandler` registry, the Engine will simply route events to isolated handler classes, restoring the Open/Closed Principle and decoupling the Engine from menu unpacking and VRAM canvas stamping logic.

**Architecture**

1. **`EventContext` (`app.game.menus.events`)**: A dataclass that holds references to the Engine's subsystems required for event resolution.
2. **`EventHandler` (`app.game.menus.handlers`)**: An abstract interface defining `handle(event: Event, context: EventContext)`.
3. **Event Router (`Engine`)**: A dictionary mapping `Type[Event]` to an instantiated `EventHandler`.

**Schema/Implementation Design**

```python
# --- DRAFT: app.game.menus.events ---
@dataclass
class EventContext:
    board: 'Board'
    screens: Dict[str, 'Screen']
    provider: 'Provider'
    bus: collections.deque

# --- DRAFT: app.game.menus.handlers ---
from abc import ABC, abstractmethod

class EventHandler(ABC):
    @abstractmethod
    def handle(self, event: Event, context: EventContext) -> None:
        pass

class TerminalEventHandler(EventHandler):
    def handle(self, event: TerminalEvent, context: EventContext) -> None:
        if context.board.menus:
            popped_menu = context.board.menus.pop()
            
            # HUD INJECTION
            if popped_menu.id == 'load':
                view_cfg = context.board.configurations.menus.get('view')
                player = context.board.player()
                if view_cfg and player:
                    screen = context.screens.get(player.state.layer, next(iter(context.screens.values())))
                    hud_menu = context.provider.unpack(
                        'view', 
                        view_cfg, 
                        {'sprite': {'state': getattr(player, 'state', None)}}, 
                        screen.screensize
                    )
                    context.board.set_overlays([hud_menu])

        if not context.board.menus:
            context.board.paused = False

```

##### Tasks

**1. Task: Event Context & Interface**

*Objective*: Define the decoupled data structures for routing.

* [ ] Subtask: In `app.game.menus.events`, define the `EventContext` dataclass.
* [ ] Subtask: Create `app.game.menus.handlers.py`. Define the abstract `EventHandler` class.

**2. Task: Handler Implementations**

*Objective*: Extract the logic from `Engine._drain()` into isolated strategy classes.

* [ ] Subtask: Implement `MenuEventHandler` in `handlers.py`.
* [ ] Subtask: Implement `StateEventHandler` in `handlers.py`.
* [ ] Subtask: Implement `TerminalEventHandler` in `handlers.py`.
* [ ] Subtask: Implement `UpdateEventHandler` in `handlers.py`.

**3. Task: Engine Router Refactor**

*Objective*: Clean the Engine loop and apply the registry.

* [ ] Subtask: In `Engine.__init__`, instantiate an `EventContext`.
* [ ] Subtask: In `Engine.__init__`, define a dictionary `self.handlers` mapping the `Event` classes to their respective `EventHandler` instances.
* [ ] Subtask: Refactor `Engine._drain()` to use a dictionary lookup: `handler = self.handlers.get(type(event))`, executing `handler.handle(event, self.event_context)`.