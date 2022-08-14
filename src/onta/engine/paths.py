import munch

import onta.settings as settings
import onta.engine.collisions as collisions
import onta.engine.static.calculator as calculator
import onta.util.logger as logger

log = logger.Logger('onta.engine.paths', settings.LOG_LEVEL)

## "STATIC" FUNCTIONS

def reorient(
    hitbox: tuple, 
    collision_set: list, 
    goal: tuple, 
    speed: int, 
    world_dim: tuple,
) -> str:
    new_up = (
        hitbox[0], 
        hitbox[1] - 2*speed - 1, 
        hitbox[2], 
        hitbox[3]
    )
    new_left = (
        hitbox[0] - 2*speed - 1, 
        hitbox[1], 
        hitbox[2], 
        hitbox[3]
    )
    new_right = (
        hitbox[0] + 2*speed + 1, 
        hitbox[1], 
        hitbox[2], 
        hitbox[3]
    )
    new_down = (
        hitbox[0], 
        hitbox[1] + 2*speed + 1, 
        hitbox[2], 
        hitbox[3]
    )

    up_valid = not collisions.detect_collision(new_up, collision_set)
    left_valid =  not collisions.detect_collision(new_left, collision_set) 
    right_valid = not collisions.detect_collision(new_right, collision_set) 
    down_valid = not collisions.detect_collision(new_down, collision_set) 

    # TODO: diagonals

    possibilities = {}

    if up_valid:
        possibilities['up'] = calculator.distance(new_up[:2], goal)
    if left_valid:
        possibilities['left'] = calculator.distance(new_left[:2], goal)
    if right_valid:
        possibilities['right'] = calculator.distance(new_right[:2], goal)
    if down_valid:
        possibilities['down'] = calculator.distance(new_down[:2], goal)
    # TODO: diagonals

    least_direction = None
    least_direction_distance = calculator.distance(( 0,0 ), world_dim)

    for key, possibility in possibilities.items():
        if possibility < least_direction_distance:
            least_direction_distance = possibility
            least_direction = key

    return least_direction


def concat_dynamic_paths(
    sprite: munch.Munch,
    hero: munch.Munch, 
    npcs: munch.Munch
) -> munch.Munch:
    pathset = sprite.memory.paths.copy()

    if sprite.stature.attention == 'hero':
        setattr(
            pathset, 
            sprite.stature.attention,
            munch.Munch({ 
                'x': hero.position.x, 'y': hero.position.y
            })
        )

    elif sprite.stature.attention in list(npcs.keys()):
        setattr(
            pathset,
            sprite.stature.attention,
            munch.Munch({
                'x': npcs.get(sprite.stature.attention).position.x,
                'y': npcs.get(sprite.stature.attention).position.y
            })
        )

    return pathset
