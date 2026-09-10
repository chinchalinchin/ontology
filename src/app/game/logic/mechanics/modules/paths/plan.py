"""
# Ontology: app.game.logic.mechanics.modules.paths.plan

Rapidly-exploring Random Tree (RRT) pathfinding implementation.
"""
import math
import random
from typing import List, Tuple

from libs.core.models import Position
import libs.core.math.geometry as geometry

class Node:
    """A node in the RRT tree."""
    __slots__ = ['x', 'y', 'parent']
    
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.parent = None

class Planner:
    """
    ## Planner (RRT)
    Generates obstacle-avoiding paths through continuous 2D space.
    """
    def __init__(
        self, 
        start: Position, 
        target: Position, 
        obstacles: List[Tuple[float, float, float, float]], 
        step_size: float = 32.0, 
        max_iter: int = 300
    ):
        self.start = Node(start.x, start.y)
        self.target = Node(target.x, target.y)
        self.obstacles = obstacles
        self.step_size = step_size
        self.max_iter = max_iter
        
        # AABB of search space with 20% padding + 2 steps buffer
        pad_w = abs(target.x - start.x) * 0.2 + step_size * 2
        pad_h = abs(target.y - start.y) * 0.2 + step_size * 2
        self.min_x = min(start.x, target.x) - pad_w
        self.max_x = max(start.x, target.x) + pad_w
        self.min_y = min(start.y, target.y) - pad_h
        self.max_y = max(start.y, target.y) + pad_h
        
        self.node_list = [self.start]

    def plan(self) -> List[Position]:
        """Executes the RRT algorithm and returns the path if found."""
        for _ in range(self.max_iter):
            rnd_node = self._sample_free_space()
            nearest_node = self._get_nearest_node(self.node_list, rnd_node)
            new_node = self._steer(nearest_node, rnd_node, self.step_size)

            if self._check_collision(nearest_node, new_node, self.obstacles):
                self.node_list.append(new_node)

                # Check if the new node is within step size of the goal
                if self._calc_dist(new_node, self.target) <= self.step_size:
                    # Final LOS check from the new node to the ultimate target
                    if self._check_collision(new_node, self.target, self.obstacles):
                        self.target.parent = new_node
                        self.node_list.append(self.target)
                        return self._generate_final_path()

        return []  # Max iterations reached without finding the goal

    def _sample_free_space(self) -> Node:
        """Samples a random point, with a 5% bias directly towards the target."""
        if random.randint(0, 100) > 5:
            return Node(
                random.uniform(self.min_x, self.max_x),
                random.uniform(self.min_y, self.max_y)
            )
        return Node(self.target.x, self.target.y)

    def _steer(self, from_node: Node, to_node: Node, step_size: float) -> Node:
        """Generates a new node a fixed step_size away from the nearest node."""
        new_node = Node(from_node.x, from_node.y)
        theta = math.atan2(to_node.y - from_node.y, to_node.x - from_node.x)
        
        new_node.x += step_size * math.cos(theta)
        new_node.y += step_size * math.sin(theta)
        new_node.parent = from_node
        
        return new_node

    def _check_collision(self, near_node: Node, new_node: Node, obstacles: List[Tuple]) -> bool:
        """Checks for intersection with any AABB using Cython segment intersections."""
        # geometry.los returns True if clear, False if blocked
        return geometry.los(near_node.x, near_node.y, new_node.x, new_node.y, obstacles)

    def _get_nearest_node(self, node_list: List[Node], rnd_node: Node) -> Node:
        """Finds the closest existing node in the tree."""
        return min(node_list, key=lambda n: self._calc_dist(n, rnd_node))

    @staticmethod
    def _calc_dist(node1: Node, node2: Node) -> float:
        return math.hypot(node1.x - node2.x, node1.y - node2.y)

    def _generate_final_path(self) -> List[Position]:
        """Backtraces the parents from the goal to the start."""
        path = []
        node = self.target
        while node.parent is not None:
            path.append(Position(x=int(node.x), y=int(node.y)))
            node = node.parent
        # Reversing ignores the start node itself, returning actionable waypoints
        return path[::-1]