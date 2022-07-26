
from onta.metaphysics \
    import settings, logger

from onta.concretion.facticity \
    import gauge
    
log = logger.Logger(
    'onta.concretion.facticity.paths', 
    settings.LOG_LEVEL
)


def reorient(
    hitbox: tuple, 
    collision_set: list, 
    goal: tuple, 
    speed: int, 
    world_dim: tuple,
) -> str:
    new_up = (
        hitbox[0], 
        hitbox[1] - 2 * speed - 1, 
        hitbox[2], 
        hitbox[3]
    )
    new_left = (
        hitbox[0] - 2 * speed - 1, 
        hitbox[1], 
        hitbox[2], 
        hitbox[3]
    )
    new_right = (
        hitbox[0] + 2 * speed + 1, 
        hitbox[1], 
        hitbox[2], 
        hitbox[3]
    )
    new_down = (
        hitbox[0], 
        hitbox[1] + 2 * speed + 1, 
        hitbox[2], 
        hitbox[3]
    )

    up_result = gauge.any_intersections(
        new_up, 
        collision_set
    )

    left_result = gauge.any_intersections(
        new_left, 
        collision_set
    )

    right_result = gauge.any_intersections(
        new_right, 
        collision_set
    )

    down_result = gauge.any_intersections(
        new_down, 
        collision_set
    )

    # TODO: diagonals

    possibilities = {}

    if up_result is None:
        possibilities['up'] = gauge.distance(
            new_up[:2], 
            goal
        )
    if left_result is None:
        possibilities['left'] = gauge.distance(
            new_left[:2], 
            goal
        )
    if right_result is None:
        possibilities['right'] = gauge.distance(
            new_right[:2], 
            goal
        )
    if down_result is None:
        possibilities['down'] = gauge.distance(
            new_down[:2], 
            goal
        )
        

    # TODO: diagonals

    least_direction = 'up'
    least_direction_distance = gauge.distance(
        ( 0,0 ), 
        world_dim
    )

    for key, possibility in possibilities.items():
        if possibility < least_direction_distance:
            least_direction_distance = possibility
            least_direction = key

    return least_direction
