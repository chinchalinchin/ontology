
import onta.engine.collisions as collisions
import onta.engine.calculator as calculator

def reorient(sprite, hitbox, collision_sets, goal, speed, world_dim) -> None:
    goal_point = (goal['x'], goal['y'])

    new_up = (hitbox[0], hitbox[1] - speed, hitbox[2], hitbox[3])
    new_left = (hitbox[0] - speed, hitbox[1], hitbox[2], hitbox[3])
    new_right = (hitbox[0] + speed, hitbox[1], hitbox[2], hitbox[3])
    new_down = (hitbox[0], hitbox[1] + speed, hitbox[2], hitbox[3])

    up_valid = all(not collisions.detect_collision(new_up, collision_set) for collision_set in collision_sets)
    left_valid = all(not collisions.detect_collision(new_left, collision_set) for collision_set in collision_sets)
    right_valid = all(not collisions.detect_collision(new_right, collision_set) for collision_set in collision_sets)
    down_valid = all(not collisions.detect_collision(new_down, collision_set) for collision_set in collision_sets)

    possibilities = {}

    if up_valid:
        possibilities['up'] = calculator.distance(new_up, goal_point)
    if left_valid:
        possibilities['left'] = calculator.distance(new_left, goal_point)
    if right_valid:
        possibilities['right'] = calculator.distance(new_right, goal_point)
    if down_valid:
        possibilities['left'] = calculator.distance(new_down, goal_point)

    least_state, least_state_distance = None, calculator.distance((0,0), world_dim)

    for key, possibility in possibilities.items():
        if possibility < least_state_distance:
            least_state_distance = possibility
            least_state = key

    if least_state == 'up':
        if 'walk' in sprite['state']:
            sprite['state'] = 'walk_up'
        elif 'run' in sprite['state']:
            sprite['state'] = 'run_up'
    elif least_state == 'down':
        if 'walk' in sprite['state']:
            sprite['state'] = 'walk_down'
        elif 'run' in sprite['state']:
            sprite['state'] = 'run_down'
    elif least_state == 'left':
        if 'walk' in sprite['state']:
            sprite['state'] = 'walk_left'
        elif 'run' in sprite['state']:
            sprite['state'] = 'run_left'
    elif least_state == 'right':
        if 'walk' in sprite['state']:
            sprite['state'] = 'walk_right'
        elif 'run' in sprite['state']:
            sprite['state'] = 'run_right'