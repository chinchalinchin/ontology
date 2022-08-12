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

    up_valid = not collisions.detect_collision('sprite', new_up, tuple(collision_set)) 
    left_valid =  not collisions.detect_collision('sprite', new_left, tuple(collision_set)) 
    right_valid = not collisions.detect_collision('sprite', new_right, tuple(collision_set)) 
    down_valid = not collisions.detect_collision('sprite', new_down, tuple(collision_set)) 

    # TODO: diagonals

    possibilities = {}

    if up_valid:
        possibilities['up'] = calculator.distance(new_up, goal)
    if left_valid:
        possibilities['left'] = calculator.distance(new_left, goal)
    if right_valid:
        possibilities['right'] = calculator.distance(new_right, goal)
    if down_valid:
        possibilities['down'] = calculator.distance(new_down, goal)
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
    npc_keys = list(npcs.keys())

    if sprite.path == 'hero':
        setattr(
            pathset, 
            sprite.path,
            munch.Munch({ 
                'x': hero.position.x, 'y': hero.position.y
            })
        )

    elif sprite.path in npc_keys:
        setattr(
            pathset,
            sprite.path,
            munch.Munch({
                'x': npcs.get(sprite.path).position.x,
                'y': npcs.get(sprite.path).position.y
            })
        )

    return pathset
