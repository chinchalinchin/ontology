"""
# Ontology: app.game.logic.modules.paths.plan

Rapidly-exploring Random Tree (RRT) pathfinding interface.
Delegates path generation to the Cythonized rrt() subroutine in libs.core.math.paths.
"""
from typing import List, Tuple

from libs.core.models import Position
from libs.core.math.paths import rrt


class Node:
    """
    Deprecated: Retained for backward compatibility.
    Inner node allocations have moved to contiguous C structures in libs.core.math.paths.
    """
    __slots__ = ['x', 'y', 'parent']

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.parent = None


class Planner:
    """
    ## Planner (RRT)
    Generates obstacle-avoiding paths through continuous 2D space.
    Thin Python wrapper unpacking models and delegating to Cython rrt().
    """
    def __init__(
        self, 
        start: Position, 
        target: Position, 
        obstacles: List[Tuple[float, float, float, float]], 
        step_size: float = 32.0, 
        max_iter: int = 300
    ):
        self.start = start
        self.target = target
        self.obstacles = obstacles
        self.step_size = step_size
        self.max_iter = max_iter

    def plan(self) -> List[Position]:
        """Executes the Cython RRT algorithm and returns the path if found."""
        return rrt(
            float(self.start.x),
            float(self.start.y),
            float(self.target.x),
            float(self.target.y),
            self.obstacles,
            float(self.step_size),
            int(self.max_iter)
        )