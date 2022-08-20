import onta.settings as settings
import onta.util.logger as logger

import onta.engine.facticity.calculator as calculator

log = logger.Logger('onta.engine.facticity.formulae', settings.LOG_LEVEL)


def _filter_nested_tuple(
    nested_tuple: tuple, 
    filter_value: str
) -> tuple:
    """_summary_

    :param nested_tuple: _description_
    :type nested_tuple: tuple
    :param filter_value: _description_
    :type filter_value: str
    :return: _description_
    :rtype: tuple 

    .. note:: 
        Assumes the first element of the tuple is the index.
    """
    for i in range(len(nested_tuple)):
        if nested_tuple[i][0] == filter_value:
            return nested_tuple[i]
    return None


def find_media_size(
    device_dim: tuple, 
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
    for i, break_point in enumerate(breakpoints):
        if device_dim[0] < break_point[0] and \
            device_dim[1] < break_point[1]:
            return sizes[i]
    return sizes[len(sizes)-1]


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
    crop_box = screen_crop_box(
        screen_dim, 
        world_dim, 
        player_dim
    )
    return calculator.intersection(
        crop_box, 
        object_dim
    )


def rotate_dimensions(
    rotator: tuple, 
    definition: str,
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
    if definition in ['left', 'right', 'horizontal'] and \
        direction == 'vertical':
        return ( rotator[1], rotator[0] )

    elif definition in ['up', 'down', 'vertical'] and \
        direction == 'horizontal':
        return ( rotator[1], rotator[0] )

    return rotator


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


def plate_coordinates(
    group_conf: tuple,
    player_dim: tuple,
    group_frame_dim: tuple, 
    tile_dim: tuple,
    world_dim: tuple,
    device_dim: tuple,
    crop: bool
) -> list:
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
    coords = list()
    for i in range(len(group_conf)):
        start = calculator.scale(
            ( group_conf[i][0], group_conf[i][1] ), 
            tile_dim,
            group_conf[i][2]
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


def wallet_coordinates(
    belt_point: tuple, #belt_rendering_points[0]
    bag_point: tuple, # bag_rendering_points[0]
    bag_dim: tuple,
    belt_dim: tuple,
    wallet_dim: tuple,
    horizontal_align: str,
    pack_margins: tuple,
) -> list:
    render_points = list()

    if horizontal_align == 'left':
        render_points.append(
            (
                belt_point[0] + \
                    (
                        belt_dim[0] + pack_margins[0] * ( bag_dim[0] + belt_dim[0] )
                    ),
                bag_point[1] + \
                    (
                        belt_dim[1] - wallet_dim[1] * (2 + pack_margins[1]) 
                    )/2
            )
        )
    else:
        render_points.append(
            (
                bag_point[0] - \
                    (
                        belt_dim[0] + pack_margins[0] * ( bag_dim[0] + belt_dim[0] )
                    ) - wallet_dim[0],
                bag_point[1] + \
                    (
                        belt_dim[1] - wallet_dim[1] * ( 2 + pack_margins[1] )
                    ) / 2
            )
        )
    render_points.append(
        (
            render_points[0][0],
            render_points[0][1] + \
                ( 1 + pack_margins[1] ) * wallet_dim[0]
        )
    )
    return render_points


def mirror_coordinates(
    device_dim: tuple,
    horizontal_align: str,
    vertical_align: str,
    stack: str,
    margins: tuple,
    padding: tuple,
    life_rank: tuple,
    life_dim: tuple
) -> list:
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
        return render_points

    # vertical
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


def slot_avatar_coordinates(
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
        slot = _filter_nested_tuple(
            slots_tuple,
            slot_key
        )

        # slot[0] = cast | thrust | slash | shoot 
        # slot[1] = equipment_name | null
        if slot and slot[1] != 'null':
            avatar = _filter_nested_tuple(
                avatar_tuple,
                slot_key
            )

            equipment = _filter_nested_tuple(
                equip_tuple,
                slot[1]
            )

            if avatar and equipment:
                slot_point = slot_points_tuple[avatar[1]]

                render_points.append(
                    (
                        ( slot_point[0] + ( slot_dim[0] - equipment[1] ) / 2 ),
                        ( slot_point[1] + ( slot_dim[1] - equipment[2] ) / 2 )
                    )
                )
                continue

        render_points.append(( -1, -1 ))

    inventory = _filter_nested_tuple(
        invent_tuple,
        bag
    )

    if inventory:
        render_points.append(
            (
                ( bag_points_tuple[0][0] + ( bag_dim[0] - inventory[1] ) / 2 ),
                ( bag_points_tuple[0][1] + ( bag_dim[1] - inventory[2] ) / 2 )
            )
        )
    else:
        render_points.append(( -1, -1 ))

    inventory = _filter_nested_tuple(
        invent_tuple,
        belt
    )

    if inventory:
        render_points.append(
            (
                ( belt_points_tuple[0][0] + ( belt_dim[0] - inventory[1] ) / 2 ), 
                ( belt_points_tuple[0][1] + ( belt_dim[1] - inventory[2] ) / 2 )
            )
        )        
    else:
        render_points.append(( -1, -1 ))

    return render_points


def idea_coordinates(
    idea_dims: list,
    num_ideas: int,
    num_pieces: int,
    device_dim: tuple,
    menu_stack: str,
    menu_margins: tuple,
    menu_padding: tuple
) -> list:
    render_points = list()
    full_width = sum(dim[0] for dim in idea_dims)

    # idea_rendering_points => len() == len(ideas)*len(pieces)
    # for (0, equipment), (1, inventory), (2, status), ...
    for i in range(num_ideas):

        # for (0, left), (1, middle), (2, right)
        # j gives you index for the piece dim in dims
        for j in range(num_pieces):

            if menu_stack == 'vertical':
                if i == 0 and j == 0:
                    x = (1 - menu_margins[0]) * device_dim[0] - full_width
                    y = menu_margins[1] * device_dim[1]
                else:
                    if j == 0:
                        x = render_points[0][0]
                        y = render_points[0][1] + \
                            (1 + menu_padding[1] ) * i * idea_dims[0][1]
                    else:
                        x = render_points[j-1][0] + \
                            idea_dims[j-1][0]
                        y = render_points[j-1][1] + \
                            (1 + menu_padding[1]) * i * idea_dims[j-1][1]

            else: # horizontal
                if i == 0 and j == 0:
                    x = menu_margins[0] * device_dim[0]
                    y = menu_margins[1] * device_dim[1]
                else:
                    if j == 0 :
                        x = render_points[0][0] + \
                            i * (full_width + menu_padding[0])
                        y = render_points[0][1]
                    else:
                        x = render_points[len(render_points)-1][0] + idea_dims[j-1][0]
                        y = render_points[j-1][1]
        
            render_points.append((x,y))
    return render_points