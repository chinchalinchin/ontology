"""
# Ontology: app.game.engine

Package for core game loop.
"""
# Standard Libraries
import time
import collections
from typing import List, Dict
import logging

# Application Libraries
import app.config.settings as settings
from app.game.board import Board
from app.game.logic.mechanics.core import Mechanic
from app.game.screen import Screen
from app.services.generators.provider import Provider
from app.game.menus.events import (
    MenuEvent, 
    TerminalEvent, 
    UpdateEvent,
    StateEvent,
    EventContext
)
from app.game.menus.handlers import (
    MenuEventHandler,
    StateEventHandler,
    TerminalEventHandler,
    UpdateEventHandler,
    EventHandler
)

logger = logging.getLogger(__name__)

class Engine:
    """
    ## Engine

    Class for running the game loop and performing framerate calculations.
    """
    board: Board
    screens: Dict[str, Screen]
    core: List[Mechanic]
    world: List[Mechanic]
    bus: collections.deque
    provider: Provider
    running: bool
    event_context: EventContext
    handlers: Dict[type, EventHandler]

    def __init__(self, 
        board: Board, 
        screens: Dict[str, Screen], 
        core: List[Mechanic],
        world: List[Mechanic],
        provider: Provider
    ):
        self.board = board
        self.screens = screens
        self.core = core
        self.world = world
        self.provider = provider
        self.bus = collections.deque()
        self.running = False
        
        # Package Engine dependencies for Event Handler distribution
        self.event_context = EventContext(
            board=self.board,
            screens=self.screens,
            provider=self.provider,
            bus=self.bus
        )
        
        # Route Event classes to their Strategy implementation
        self.handlers = {
            MenuEvent: MenuEventHandler(),
            StateEvent: StateEventHandler(),
            TerminalEvent: TerminalEventHandler(),
            UpdateEvent: UpdateEventHandler()
        }

    @staticmethod
    def time() -> float:
        return time.perf_counter()

    def _drain(self) -> None:
        """
        Drains the event bus and routes events to their handlers.
        """
        while self.bus:
            event = self.bus.popleft()
            handler = self.handlers.get(type(event))
            
            if handler:
                handler.handle(event, self.event_context)
            else:
                logger.warning(f"No Event Handler registered for type: {type(event)}")

    def _play(self, delta) -> None:
        """
        Apply Mechanics.
        """
        payload = self.board.device.poll()
        for mechanic in self.core:
            mechanic.update(self.board, delta, self.bus, payload)

        if not self.board.paused and self.board.loaded:
            for mechanic in self.world:
                mechanic.update(self.board, delta, self.bus, payload)

    def _render(self) -> None:
        """
        Render Assets.
        """
        player = self.board.player()
        
        # Trap the rendering flow if we are in MainMenu or Loading mode
        if not self.board.loaded or not player:
            screen = next(iter(self.screens.values()))
            screen.clear()
            screen.interface(self.board.menus, self.board.overlays)
            screen.present()
            return
            
        screen = self.screens[player.state.layer]
        screen.clear()
        screen.draw(
            self.board.renderables(player.state.layer), 
            player.state.position,
            player.dimensions
        )
        screen.interface(
            self.board.menus, 
            self.board.overlays
        )
        screen.present()

    def start(self) -> None:        
        logger.info("Entering Game Loop...")

        delta = 1.0 / settings.TARGET_FPS
        accumulator = 0.0
        spin_threshold = 0.002 
        last_time = self.time()

        telemetry_frames = 0
        telemetry_updates = 0
        telemetry_start_time = last_time

        self.running = True
        while self.running:
            current_time = self.time()
            frame_time = current_time - last_time
            last_time = current_time
            accumulator += frame_time
            
            # Fixed-timestep Logic Updates
            while accumulator >= delta:
                self._play(delta)
                self._drain()

                accumulator -= delta
                telemetry_updates += 1

            self._render()
            telemetry_frames += 1

            #  Hybrid Pacing (Sleep + Spin)
            work_time = self.time() - current_time
            sleep_time = delta - work_time
            
            if sleep_time > 0:
                if sleep_time > spin_threshold:
                    time.sleep(sleep_time - spin_threshold)
                
                while (self.time() - current_time) < delta:
                    pass

            if telemetry_frames % 600 == 0:
                elapsed = self.time() - telemetry_start_time
                avg_fps = telemetry_frames / elapsed
                avg_ups = telemetry_updates / elapsed
                
                logger.info(f"[TELEMETRY] Avg FPS: {avg_fps:.1f} |"
                            f"Avg UPS (Ticks): {avg_ups:.1f}")
                
                telemetry_frames = 0
                telemetry_updates = 0
                telemetry_start_time = self.time()