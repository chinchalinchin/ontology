from numba import njit
from numba.pycc import CC

import onta.settings as settings
import onta.util.logger as logger
import onta.engine.static.calculator as calculator


cc = CC("formulae")

log = logger.Logger('onta.engine.static.formulae', settings.LOG_LEVEL)

@njit
@cc.export(
    'screen_crop_box',
    'UniTuple(float64,4)(UniTuple(float64,2),UniTuple(float64,2),UniTuple(float64,2))'
)
def screen_crop_box(
    screen_dim: tuple, 
    world_dim: tuple, 
    hero_pt: tuple
) -> tuple:
    # TODO: should be based on hero's center, not top left corner
    left_breakpoint = screen_dim[0]/2
    right_breakpoint = world_dim[0] - screen_dim[0]/2
    top_breakpoint = screen_dim[1]/2
    bottom_breakpoint = world_dim[1] - screen_dim[1]/2

    if hero_pt[0] >= 0 and hero_pt[0] <= left_breakpoint:
        crop_x = 0
    elif hero_pt[0] > right_breakpoint:
        crop_x = world_dim[0] - screen_dim[0]
    else:
        crop_x = hero_pt[0] - screen_dim[0]/2

    if hero_pt[1] >= 0 and hero_pt[1] <= top_breakpoint:
        crop_y = 0
    elif hero_pt[1] > bottom_breakpoint:
        crop_y = world_dim[1] - screen_dim[1]
    else:
        crop_y = hero_pt[1] - screen_dim[1]/2

    crop_width = crop_x + screen_dim[0]
    crop_height = crop_y + screen_dim[1]
    return (crop_x, crop_y, crop_width, crop_height)

@njit
@cc.export(
    'on_screen',
    'boolean(UniTuple(float64,4),UniTuple(float64,4),UniTuple(float64,2),UniTuple(float64,2))'
)
def on_screen(
    player_dim: tuple,
    object_dim: tuple,
    screen_dim: tuple,
    world_dim: tuple
) -> bool:
    """_summary_

    :param player_dim: (x,y,w,h)
    :type player_dim: tuple
    :param object_dim: (x,y,w,h)
    :type object_dim: tuple
    :param screen_dim: (x,y,w,h)
    :type screen_dim: tuple
    :param world_dim: (x,y,w,h)
    :type world_dim: tuple
    :return: _description_
    :rtype: bool
    """
    crop_box = screen_crop_box(screen_dim, world_dim, player_dim)
    return calculator.intersection(crop_box, object_dim)


@njit
@cc.export(
    'tile_coordinates',
    'List(UniTuple(int64,2))(UniTuple(int64,2),UniTuple(int64,2),UniTuple(int64,2))'
)
def tile_coordinates(
    set_dim: tuple,
    start: tuple,
    tile_dimensions: tuple
) -> list:
    dims = []
    for i in range(set_dim[0]):
        for j in range(set_dim[1]):
            dims.append(
                (
                    start[0] + tile_dimensions[0]*i, 
                    start[1] + tile_dimensions[1]*j
                )
            )
    return dims


@njit
@cc.export(
    'plate_coordinates',
    'List(Tuple((int64,float64,float64)),reflected=False)(List(Tuple((float64,float64,unicode_type)),reflected=False),UniTuple(float64,4),UniTuple(float64,2),UniTuple(int64,2),UniTuple(int64,2),UniTuple(int64,2),boolean)'
)
def plate_coordinates(
    group_conf: list,
    player_dim: tuple,
    group_frame_dim: tuple, 
    tile_dim: tuple,
    world_dim: tuple,
    device_dim: tuple,
    crop: bool
) -> tuple:
    """_summary_

    :param group_configuration: _description_
    :type group_configuration: dict
    :param group_frame_dim: _description_
    :type group_frame_dim: tuple
    :param world_dim: _description_
    :type world_dim: tuple
    :param device_dim: _description_
    :type device_dim: tuple
    :param crop: _description_
    :type crop: bool
    :return: _description_
    :rtype: list

    .. note:: 
        The first field in each element of the returned list is the index of the group frame.
    """
    coords = []
    for i, set_conf in enumerate(iter(group_conf)):
        start = calculator.scale(
            ( set_conf[0], set_conf[1] ), 
            tile_dim,
            set_conf[2]
        )
        object_dim = (
            start[0],
            start[1],
            group_frame_dim[0],
            group_frame_dim[1]
        )

        if crop and not on_screen(
            player_dim, 
            object_dim, 
            device_dim, 
            world_dim
        ):
            continue 
        
        coords.append((i, start[0], start[1]))
    return coords

