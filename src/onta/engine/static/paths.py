
from numba.pycc import CC
from numba import njit

import onta.settings as settings
import onta.engine.static.calculator as calculator
import onta.util.logger as logger

log = logger.Logger('onta.engine.static.paths', settings.LOG_LEVEL)

cc = CC('paths')


@njit
@cc.export(
    'reorient',
    'unicode_type(UniTuple(float64,4),List(UniTuple(float64,4)),UniTuple(float64,2),int64,UniTuple(int64,2))'
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

    # compiled version returns all -1 instead of None to avoid type-check problems

    up_result = calculator.any_intersections(
        new_up, 
        collision_set
    )
    up_valid = len([
        el 
        for el in iter(up_result)
        if el == -1
    ]) > 0

    left_result = calculator.any_intersections(
        new_left, 
        collision_set
    )
    left_valid = len([
        el 
        for el in iter(left_result)
        if el == -1
    ]) > 0


    right_result = calculator.any_intersections(
        new_right, 
        collision_set
    )
    right_valid = len([
        el 
        for el in iter(right_result)
        if el == -1
    ]) > 0

    down_result = calculator.any_intersections(
        new_down, 
        collision_set
    )
    down_valid = len([
        el 
        for el in iter(down_result)
        if el == -1
    ]) > 0
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

    least_direction = ''
    least_direction_distance = calculator.distance(( 0,0 ), world_dim)

    for key, possibility in possibilities.items():
        if possibility < least_direction_distance:
            least_direction_distance = possibility
            least_direction = key

    return least_direction
