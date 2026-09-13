import math
import random

class Node:
    """A node in the RRT tree."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.parent = None

class RRT:
    def __init__(self, start, goal, obstacle_list, rand_area, step_size=1.0, max_iter=500):
        self.start = Node(start[0], start[1])
        self.goal = Node(goal[0], goal[1])
        self.min_rand, self.max_rand = rand_area
        self.step_size = step_size
        self.max_iter = max_iter
        self.obstacle_list = obstacle_list
        self.node_list = [self.start]

    def plan(self):
        """Executes the RRT algorithm and returns the path if found."""
        for _ in range(self.max_iter):
            rnd_node = self._sample_free_space()
            nearest_node = self._get_nearest_node(self.node_list, rnd_node)
            new_node = self._steer(nearest_node, rnd_node, self.step_size)

            if self._check_collision(nearest_node, new_node, self.obstacle_list):
                self.node_list.append(new_node)

                # Check if the new node is within step size of the goal
                if self._calc_dist(new_node, self.goal) <= self.step_size:
                    self.goal.parent = new_node
                    self.node_list.append(self.goal)
                    return self._generate_final_path()

        return None  # Max iterations reached without finding the goal

    def _sample_free_space(self):
        """Samples a random point in the defined continuous area."""
        # 5% chance to bias the sample directly at the goal to pull the tree forward
        if random.randint(0, 100) > 5:
            return Node(
                random.uniform(self.min_rand, self.max_rand),
                random.uniform(self.min_rand, self.max_rand)
            )
        return Node(self.goal.x, self.goal.y)

    def _steer(self, from_node, to_node, step_size):
        """Generates a new node a fixed step_size away from the nearest node."""
        new_node = Node(from_node.x, from_node.y)
        theta = math.atan2(to_node.y - from_node.y, to_node.x - from_node.x)
        
        new_node.x += step_size * math.cos(theta)
        new_node.y += step_size * math.sin(theta)
        new_node.parent = from_node
        
        return new_node

    def _check_collision(self, near_node, new_node, obstacle_list):
        """Checks for intersection with any circular obstacle using point-line segment distances."""
        for (ox, oy, size) in obstacle_list:
            dx = new_node.x - near_node.x
            dy = new_node.y - near_node.y
            dist = math.hypot(dx, dy)
            
            # Sub-step along the segment to ensure the line doesn't cut through a circle
            steps = int(dist / (self.step_size / 2))
            for i in range(steps + 1):
                px = near_node.x + dx * (i / steps) if steps > 0 else near_node.x
                py = near_node.y + dy * (i / steps) if steps > 0 else near_node.y
                
                if math.hypot(px - ox, py - oy) <= size:
                    return False  # Collision detected
        return True  # Collision-free

    def _get_nearest_node(self, node_list, rnd_node):
        """Finds the closest existing node in the tree to the randomly sampled point."""
        distances = [(self._calc_dist(node, rnd_node), node) for node in node_list]
        distances.sort(key=lambda x: x[0])
        return distances[0][1]

    @staticmethod
    def _calc_dist(node1, node2):
        return math.hypot(node1.x - node2.x, node1.y - node2.y)

    def _generate_final_path(self):
        """Backtraces the parents from the goal to the start."""
        path = [[self.goal.x, self.goal.y]]
        node = self.goal.parent
        while node.parent is not None:
            path.append([node.x, node.y])
            node = node.parent
        path.append([self.start.x, self.start.y])
        return path[::-1] # Reverse to output start-to-finish

# Example Usage
if __name__ == '__main__':
    start_pos = (0.0, 0.0)
    goal_pos = (15.0, 15.0)
    # Format: (x, y, radius)
    obstacles = [(5.0, 5.0, 2.0), (8.0, 10.0, 3.0), (12.0, 5.0, 2.0)]
    bounds = (0.0, 20.0)

    rrt = RRT(start=start_pos, goal=goal_pos, obstacle_list=obstacles, rand_area=bounds, step_size=1.5)
    path = rrt.plan()

    if path:
        print("Path successfully found:")
        for point in path:
            print(f"({point[0]:.2f}, {point[1]:.2f})")
    else:
        print("Path blocked or max iterations reached.")