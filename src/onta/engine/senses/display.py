import functools

import munch
import numba

from onta import device
from onta.engine.static import calculator, formulae
import onta.util.helper as helper

def construct_themes(
    themes:munch.Munch
) -> None:
    """Convert nested RGBA map into tuple accessible through dot notation, `theme.theme_component`.

    :param themes: _description_
    :type themes: munch.Munch
    :return: _description_
    :rtype: _type_
    """
    theme = munch.Munch({})
    for theme_key, theme_map in themes.items():
        setattr(
            theme, 
            theme_key, 
            (
                theme_map.r, 
                theme_map.g, 
                theme_map.b, 
                theme_map.a
            )
        )
    return theme


def format_breakpoints(
    break_points: list
) -> list:
    """_summary_

    :param break_points: _description_
    :type break_points: list
    :return: _description_
    :rtype: list
    """
    return [
        (break_point.w, break_point.h) 
            for break_point in break_points
    ]


def rotate_dimensions(
    rotator: munch.Munch, 
    direction: str
) -> tuple:
    """The width and height of a cap relative to a direction, `vertical` or `horizontal`.

    :param cap: _description_
    :type cap: _type_
    :param direction: _description_
    :type direction: _type_
    :return: _description_
    :rtype: _type_
    """
    if rotator.definition in ['left', 'right', 'horizontal']:
        if direction =='horizontal':
            return ( rotator.size.w, rotator.size.h )
        if direction == 'vertical':
            return ( rotator.size.h, rotator.size.w )
    elif rotator.definition in ['up', 'down', 'vertical']:
        if direction == 'horizontal':
            return ( rotator.size.h, rotator.size.w )
        if direction == 'vertical':
            return ( rotator.size.w, rotator.size.h )


def find_media_size(
    player_device: device.Device, 
    sizes: list, 
    breakpoints: list
) -> str:
    """Iterate through ordered breakpoints and compare to screen dimensions until media size is found.

    :param player_device: Object representing the player device.
    :type player_device: device.Device
    :param sizes: List of sizes for the breakpoints, i.e. `len(sizes) == len(breakpoints) - 1`. So, if `sizes = ['small', 'large']` and `breakpoints = [(800,600)]`, then if the screen is (600,400), the size 'small' will be selected, where if screen is (900, 500) the size 'large' will be selected. 
    :type sizes: list
    :param breakpoints: List of tuples representing the points at which styles and layouts shift to accomodate a new screen sie.
    :type breakpoints: list
    :return: The name of the size within the breakpoint.
    :rtype: str
    """
    dim = player_device.dimensions
    for i, break_point in enumerate(breakpoints):
        if dim[0] < break_point[0] and dim[1] < break_point[1]:
            return sizes[i]
    return sizes[len(sizes)-1]



# only needs called once, so no jit.
def bag_coordinates(
    piece_sizes: tuple,
    pack_dim: tuple,
    horizontal_align: str,
    vertical_align: str,
    margin_percents: tuple,
    margin_ref: tuple
):
    render_points = list()
    prev_w = 0

    # (0, (left.w, left.h)), (1, (right.w, right.h)) ...
    for i, piece_size in enumerate(piece_sizes):
        if i == 0:
            if horizontal_align == 'left':
                x = margin_percents[0] * margin_ref[0]

            elif horizontal_align == 'right':
                x = ( 1 - margin_percents[0] ) * margin_ref[0] - \
                    pack_dim[0]

            if vertical_align == 'top':
                y = margin_percents[1] * margin_ref[1]

            elif vertical_align == 'bottom':
                y = ( 1 - margin_percents[0] ) * margin_ref[1] - \
                    pack_dim[1]

        else:
            x = render_points[i-1][0] + prev_w
            y = render_points[i-1][1]
        render_points.append((x,y))
        prev_w = piece_size[0]

    return render_points


# only needs called once, so no jit.
# see next notes though
def belt_coordinates(
    initial_position: tuple,
    piece_sizes: tuple,
    pack_dim: tuple,
    horizontal_align: str,
    margin_percents: tuple,
    margin_ref: tuple,
    centering: tuple
) -> list:
    render_points = list()
    prev_w = 0
    # belt initial position only affected by pack vertical alignment
    for i, piece_size in enumerate(piece_sizes):
        if i == 0:
            if horizontal_align == 'left':
                # dependent on bag height > belt height
                x = initial_position[0] + \
                        ( 1 + margin_percents[0] ) * margin_ref[0]
                y = initial_position[1] + \
                        ( centering[1] - pack_dim[1] )/2

            elif horizontal_align == 'right':
                x = initial_position[0] - \
                        ( 1 + margin_percents[0] ) * margin_ref[0]
                y = initial_position[1] + \
                        ( centering[1] - pack_dim[1] )/2  
        else:
            x = render_points[i-1][0] + prev_w
            y = render_points[i-1][1]
        render_points.append((x,y))
        prev_w = piece_size[0]
    
    return render_points


# only needs called once, so no jit.
# see next note, though
def mirror_coordinates(
    device_dim: tuple,
    horizontal_align: str,
    vertical_align: str,
    stack: str,
    margins: tuple,
    padding: tuple,
    life_rank: tuple,
    life_dim: tuple
):
    render_points = list()

    if horizontal_align == 'right':
        x_start = device_dim[0] - margins[0] - \
            life_rank[0] * life_dim[0]*(1 + padding[0]) 
    elif horizontal_align == 'left':
        x_start = margins[0]
    else: # center
        x_start = (device_dim[0] - \
            life_rank[0] * life_dim[0] *(1 + padding[0]))/2
    
    if vertical_align == 'top':
        y_start = margins[1]
    elif vertical_align == 'bottom':
        y_start = device_dim[1] - margins[1] - \
            life_rank[1] * life_dim[1] * (1 + padding[1])
    else: # center
        y_start = (device_dim[1] - \
            life_rank[1] * life_dim[1] * (1 + padding[1]))/2


    if stack== 'vertical':
        life_rank = (life_rank[1], life_rank[0])
        
    for row in range(life_rank[1]):
        for col in range(life_rank[0]):

            if (row+1)*col == 0:
                render_points.append(
                    ( x_start, y_start)
                )
                continue
            elif stack == 'horizontal':
                render_points.append(
                    (
                        render_points[(row+1)*col - 1][0] + \
                            life_dim[0]*(1+padding[0]),
                        render_points[(row+1)*col - 1][1]
                    )
                )
                continue
            render_points.append(
                (
                    render_points[(row+1)*col - 1][0] + \
                        life_dim[0],
                    render_points[(row+1)*col - 1][1] + \
                        life_dim[1]*(1+padding[1])
                )
            )
            continue
    return render_points


# no jit or cache...
# only needs called once, unless user is given ability to restyle hud?
#   not a bad idea...
def slot_coordinates(
    slots_total: int,
    slot_dim: tuple,
    buffer_dim: tuple,
    cap_dim: tuple,
    device_dim: tuple,
    horizontal_align: str,
    vertical_align: str,
    stack: str,
    margins: tuple
) -> list:
    render_points = list()

    if horizontal_align == 'right':
        x_start = device_dim[0] \
            - margins[0] * device_dim[0] \
            - slots_total * slot_dim[0] \
            - ( slots_total - 1 ) * buffer_dim[0] \
            - 2 * cap_dim[0]
    elif horizontal_align == 'center':
        x_start = ( device_dim[0] \
            - slots_total*slot_dim[0] \
            - ( slots_total-1)*buffer_dim[0] \
            - 2*cap_dim[0] )/2
            
    else: # left
        x_start = margins[0] * device_dim[0]

            
    if vertical_align == 'bottom':
        if stack == 'horizontal':
            y_start = device_dim[1] \
                - margins[1] * device_dim[1] \
                - slot_dim[1] 
        elif stack == 'vertical':
            y_start = device_dim[1] \
                - margins[1] * device_dim[1] \
                - slots_total * slot_dim[1] \
                - ( slots_total - 1 ) * buffer_dim[1] \
                - 2 * cap_dim[1]
    elif vertical_align == 'center':
        y_start = (device_dim[1] \
            - slots_total * slot_dim[1] \
            - (slots_total - 1 ) * buffer_dim[1] \
            - 2 * cap_dim[1] )/2
    else: # top
        y_start = margins[1] * device_dim[1]

    # 0    1     2       3     4       5     6       7     8
    # cap, slot, buffer, slot, buffer, slot, buffer, slot, cap
    # number of slots + number of buffers + number of caps
    num = slots_total + (slots_total - 1) + 2
    if stack == 'horizontal':
        buffer_correction = (slot_dim[1] - buffer_dim[1])/2
        cap_correction = (slot_dim[1] - cap_dim[1])/2 

        for i in range(num):
            if i == 0: # cap
                render_points.append(
                    ( x_start, y_start + cap_correction )
                )
            elif i == 1: # slot
                render_points.append(
                    ( render_points[i-1][0] + cap_dim[0], y_start )
                )
            elif i == num - 1: # cap
                render_points.append(
                    ( 
                        render_points[i-1][0] + slot_dim[0], 
                        y_start + cap_correction
                    )
                )
            elif i % 2 == 0: # buffer
                render_points.append(
                    (
                        render_points[i-1][0] + slot_dim[0], 
                        y_start + buffer_correction
                    )
                )
            else: # slot
                render_points.append(
                    ( render_points[i-1][0] + buffer_dim[0], y_start )
                )

    elif stack == 'vertical':
        buffer_correction = (slot_dim[0] - buffer_dim[0])/2
        cap_correction = (slot_dim[0] - cap_dim[0])/2
        for i in range(num):
            if i == 0: # cap
                render_points.append(
                    ( x_start + cap_correction, y_start )
                )
            elif i == 1: # slot
                render_points.append(
                    ( x_start, render_points[i-1][1] + cap_dim[1] )
                )
            elif i == num - 1: # cap
                render_points.append(
                    (
                        x_start + cap_correction,
                        render_points[i-1][1] + slot_dim[1]
                    )
                )
            elif i % 2 == 0: # buffer
                render_points.append(
                    (
                        x_start + buffer_correction,
                        render_points[i-1][1] + slot_dim[1]
                    )
                )
            else: # slot
                render_points.append(
                    (
                        x_start,
                        render_points[i-1][1] + buffer_dim[1]
                    )
                )
    return render_points


@functools.lru_cache(maxsize=100)
@numba.jit(nopython=True, nogil=True, fastmath=True)
def avatar_coordinates(
    slots_tuple: tuple,
    equip_tuple: tuple,
    invent_tuple: tuple,
    slot_points_tuple: tuple,
    bag_points_tuple: tuple,
    belt_points_tuple: tuple,
    map_tuple: tuple,
    avatar_tuple: tuple,
    bag: str,
    belt: str,
    slot_dim: tuple,
    bag_dim: tuple,
    belt_dim: tuple,
) -> list:
    render_points = list()
    
    for slot_key in iter(map_tuple):

        slot = helper.filter_nested_tuple(
            slots_tuple,
            slot_key
        )

        # slot[0] = cast | thrust | slash | shoot
        # slot[1] = equipment_name
        if slot and slot[0][1] != 'null':
            avatar = helper.filter_nested_tuple(
                avatar_tuple, 
                slot_key
            )

            equipment = helper.filter_nested_tuple(
                equip_tuple,
                slot[0][1]
            )

            if avatar and equipment:
                equipment = equipment
                avatar = avatar

                slot_point = slot_points_tuple[avatar[0][1]]

                render_points.append(
                    (
                        ( slot_point[0] + ( slot_dim[0] - equipment[0][1] ) / 2 ),
                        ( slot_point[1] + ( slot_dim[1] - equipment[0][2] ) / 2 )
                    )
                )
                continue

        render_points.append(( -1, -1 ))

    inventory = helper.filter_nested_tuple(
        invent_tuple,
        bag
    )

    if inventory:
        render_points.append(
            (
                ( bag_points_tuple[0][0] + ( bag_dim[0] - inventory[0][1] ) / 2 ),
                ( bag_points_tuple[0][1] + ( bag_dim[1] - inventory[0][2] ) / 2 )
            )
        )
    else:
        render_points.append(( -1, -1 ))

    inventory = helper.filter_nested_tuple(
        invent_tuple,
        belt
    )

    if inventory:
        render_points.append(
            (
                ( belt_points_tuple[0][0] + ( belt_dim[0] - inventory[0][1] ) / 2 ), 
                ( belt_points_tuple[0][1] + ( belt_dim[1] - inventory[0][2] ) / 2 )
            )
        )        
    else:
        render_points.append(( -1, -1 ))

    return render_points

