import onta.settings as settings
import onta.util.logger as logger
import onta.engine.static.calculator as calculator

log = logger.Logger('onta.engine.static.formulae', settings.LOG_LEVEL)


def filter_nested_tuple(
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
    iter_tup = iter(nested_tuple)
    filtered = tuple(
        tup
        for tup in iter_tup
        if tup[0] == filter_value
    )
    
    return filtered


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
    crop_box = screen_crop_box(screen_dim, world_dim, player_dim)
    return calculator.intersection(crop_box, object_dim)


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
        slot = filter_nested_tuple(
            slots_tuple,
            slot_key
        )

        # slot[0] = cast | thrust | slash | shoot
        # slot[1] = equipment_name
        if slot and slot[0][1] != 'null':
            avatar = filter_nested_tuple(
                avatar_tuple,
                slot_key
            )

            equipment = filter_nested_tuple(
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

    inventory = filter_nested_tuple(
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

    inventory = filter_nested_tuple(
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


