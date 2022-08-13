import functools
import munch
import numba

import onta.settings as settings
import onta.util.logger as logger
import onta.engine.static.calculator as calculator


log = logger.Logger('onta.engine.formulae', settings.LOG_LEVEL)


@numba.jit(nopython=True, nogil=True, fastmath=True)
def filter_nested_tuple_by_value(
    nested_tuple: tuple, 
    filter_value: str
) -> tuple:
    filtered = [
        tup
        for tup in iter(nested_tuple)
        if tup[0] == filter_value
    ]
    
    return filtered


@numba.jit(nopython=True, nogil=True, fastmath=True)
def filter_nested_tuple_by_index(
    nested_tuple: tuple, 
    filter_index: int, 
) -> tuple:
    filtered = [
        tup
        for i, tup in enumerate(iter(nested_tuple))
        if i == filter_index
    ]

    return filtered


@numba.jit(nopython=True, nogil=True, fastmath=True)
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


@numba.jit(nopython=True, nogil=True, fastmath=True)
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


@numba.jit(nopython=True, nogil=True)
def decompose_animate_stature(
    sprite_stature:str
) -> tuple:
    split = sprite_stature.split(settings.SEP)
    return (split[0], split[1])


@numba.jit(nopython=True, nogil=True, fastmath=True)
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


@numba.jit(nopython=True, nogil=True, fastmath=True)
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

            elif vertical_align == 'bottoms':
                y = ( 1 - margin_percents[0] ) * margin_ref[1] - \
                    pack_dim[0]

        else:
            x = render_points[i-1][0] + prev_w
            y = render_points[i-1][1]
        render_points.append((x,y))
        prev_w = piece_size[0]

    return render_points


@numba.jit(nopython=True, nogil=True, fastmath=True)
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


@numba.jit(nopython=True, nogil=True, fastmath=True)
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


@functools.lru_cache(maxsize=100)
@numba.jit(nopython=True, nogil=True, fastmath=True)
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

        slot = filter_nested_tuple_by_value(
            slots_tuple,
            slot_key
        )

        # slot[0] = cast | thrust | slash | shoot
        # slot[1] = equipment_name
        if slot and slot[0][1] != 'null':
            avatar = filter_nested_tuple_by_value(
                avatar_tuple, 
                slot_key
            )

            equipment = filter_nested_tuple_by_value(
                equip_tuple,
                slot[0][1]
            )

            if avatar and equipment:
                equipment = equipment
                avatar = avatar

                slot_point = filter_nested_tuple_by_index(
                    slot_points_tuple,
                    avatar[0][1]
                )

                if slot_point:              
                    render_points.append(
                        (
                            ( slot_point[0][0] + ( slot_dim[0] - equipment[0][1] ) / 2 ),
                            ( slot_point[0][1] + ( slot_dim[1] - equipment[0][2] ) / 2 )
                        )
                    )
                    continue

        render_points.append(( -1, -1 ))

    inventory = filter_nested_tuple_by_value(
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

    inventory = filter_nested_tuple_by_value(
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


@functools.lru_cache(maxsize=200)
def plate_coordinates(
    group_conf: tuple,
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
    return tuple(coords)


def construct_animate_statures(
    stature_props: munch.Munch
) -> list:
    animate_statures = []
    for action in stature_props.decomposition.animate:
        if action != stature_props.decomposition.end:
            for direction in stature_props.decomposition.directions.real:
                animate_statures.append(
                    settings.SEP.join([action, direction])
                )
        else:
            animate_statures.append(action)

    return animate_statures


def compose_animate_stature(
    sprite: munch.Munch,
    stature_props: munch.Munch
) -> str:
    """_summary_

    :param sprite: _description_
    :type sprite: munch.Munch
    :param stature_props: _description_
    :type stature_props: munch.Munch
    :return: _description_
    :rtype: _type_

    .. note::
        The diagonal directions get collapsed into a single direction due to the spritesheet specifications. If, in the future, spritesheets with a more robust frameset are added, this method will need updated to reflect the new directions available.
    """
    up_left = settings.SEP.join(['up', 'left'])
    down_left = settings.SEP.join(['down', 'left'])
    up_right = settings.SEP.join(['up', 'right'])
    down_right = settings.SEP.join(['down', 'right'])

    if not sprite.stature or not sprite.stature.action:
        # default state. setting?
        return settings.SEP.join([ 
            settings.DEFAULT_SPRITE_ACTION, 
            settings.DEFAULT_SPRITE_DIRECTION
        ])
    if sprite.stature.action in stature_props.decomposition.singular or \
        sprite.stature.action in stature_props.decomposition.end:
        return settings.SEP.join([
            settings.DEFAULT_SPRITE_ACTION, 
            sprite.stature.direction
        ])
    elif sprite.stature.direction in [ up_left, down_left ]:
        return settings.SEP.join([
            sprite.stature.action, 
            'left'
        ])
    elif sprite.stature.direction in [ up_right, down_right ]:
        return settings.SEP.join([
            sprite.stature.action ,
            'right'
        ])
    return settings.SEP.join([
        sprite.stature.action, 
        sprite.stature.direction
    ])


def decompose_compositions_into_sets(
    layers: list,
    compositions: munch.Munch,
    composition_conf: munch.Munch,
    tile_dimensions: tuple,
    tilesets: munch.Munch,
    strutsets: munch.Munch,
    platesets: munch.Munch,
) -> tuple:
    """Decompose _Composite_ _Form_\s, or "compositions", into their constituent formsets and append to existing formsets.

    :param layers: List of layers containing compositions.
    :type layers: list
    :param compositions: Dictionary containing the constituent form sets of a composition.
    :type compositions: dict
    :param composition_conf: _Composite_ configuration information.
    :type composition_conf: dict
    :param tile_dimensions: Dimensions of a _Tile_.
    :type tile_dimensions: tuple
    :param tilesets: Existing tilesets in the world. If composition contains tiles, these _Tile_\s will be appended to the tilesets. 
    :type tilesets: dict
    :param strutsets: Existing strutsets in the world. If composition contains struts, these _Strut_\s will be appended to the strutsets.
    :type strutsets: dict
    :param platesets: Existing platesets in the world. If composition contains plates, these _Plate_\s will be appended to the platesets.
    :type platesets: dict
    :return: tu
    :rtype: tuple containing (tilesets, strutsets, platesets) with composition sets appended

    .. note::
        This method must be called before stationary hitboxes are initialized, since this method decomposes compositions into their consistuent sets and appends them to the existing static state. Otherwise, the compositions will not be rendered on the _View_ or interactable within the _World_.
    """
    log.debug(f'Decomposing composite static world state into constituents...', 
        'decompose_compositions')

    decomposition = [
        tilesets.copy(),
        strutsets.copy(),
        platesets.copy()
    ]
    
    # for layer_one, layer_two, ...
    for layer in layers:
        log.verbose(
            f'Searching for composition on layer: {layer}',
            'decompose_compositions_into_sets'
        )
        if compositions.get(layer) is None:
            continue

        # for (house, {composition}), (tree_patch, {composition}) ...
        for composite_key, composition in compositions.get(layer).items():
            log.verbose(f'Decomposing {composite_key} composition...', 
                'decompose_compositions_into_sets')

            # NOTE: composition = { 'order': int, 'sets': [ ... ] }
            #           via compose state information (static.yaml)
            for composeset in composition.sets:

                # RETRIEVE STATIC STATE INSERTION

                # NOTE: composeset = { 'start': { ... } }
                #           via compose state information (static.yaml)
                compose_start = calculator.scale(
                    ( composeset.start.x, composeset.start.y),
                    tile_dimensions,
                    composeset.start.units
                )

                # ITERATE OVER COMPOSITION CONFIGURATION FOR EACH STATIC INSERATION

                # NOTE: composition_conf[composite_key] = { 'struts': { ... }, 'plates': { ... } }
                #           via compose configuration information (composite.yaml)
                for elementset_key, elementset_conf in composition_conf.get(composite_key).items():
                    # NOTE: elementset_conf = { 'element_key': { 'order': int, 'sets': [ ... ] } }
                    #           via compose element configuration (composite.yaml)
                    log.verbose(f'Decomposing {elementset_key}...', 
                        'decompose_compositions_into_sets')

                    # GRAB EXISTING ASSETS
                    if elementset_key == 'tiles':
                        buffer_sets = decomposition[0]
                    elif elementset_key == 'struts':
                        buffer_sets = decomposition[1]
                    elif elementset_key == 'plates':
                        buffer_sets = decomposition[2]

                    for element_key, element in elementset_conf.items():
                        log.verbose(
                            f'Decomposing {element_key}...', 
                            'decompose_compositions_into_sets'
                        )

                        # NOTE: element['sets'] = [ { 'start': {..}, 'cover': bool } ]
                        #            via compose element configuration (composite.yaml)
                        for elementset in element.sets:
                            log.verbose(
                                f'Inserting {element_key} set', 
                                'decompose_compositions_into_sets'
                            )
                            
                            # NOTE elementset = { 'start': { ... }, 'cover': bool }
                            #       via compose element configuration (composite.yaml)

                            if not buffer_sets.get(layer):
                                setattr(buffer_sets, layer, munch.Munch({}))
                            
                            if not buffer_sets.get(layer).get(element_key):
                                setattr(buffer_sets.get(layer), element_key, munch.Munch({}))

                            if not buffer_sets.get(layer).get(element_key).get('sets'):
                                log.verbose('Set empty...', 'decompose_composition_into_sets')
                                setattr(
                                    buffer_sets.get(layer).get(element_key),
                                    'sets',
                                    []
                                )

                            if not buffer_sets.get(layer).get(element_key).get('order') and \
                                 buffer_sets.get(layer).get(element_key).get('order') != 0:
                                log.verbose(
                                    f'Generating render order for new set: {len(buffer_sets.get(layer))}', 
                                    'decompose_compositions_into_sets')
                                setattr(
                                    buffer_sets.get(layer).get(element_key),
                                    'order',
                                    len(buffer_sets.get(layer))
                                )
                    
                            if elementset_key == 'plates':
                                buffer_sets.get(layer).get(element_key).sets.append(
                                    munch.Munch({
                                        'start': {
                                            'units': elementset.start.units,
                                            'x': compose_start[0] + elementset.start.x,
                                            'y': compose_start[1] + elementset.start.y,
                                        },
                                        'cover': elementset.cover,
                                        'content': elementset.content

                                    })
                                )
                            else:
                                buffer_sets.get(layer).get(element_key).sets.append(
                                    munch.Munch({
                                        'start': {
                                            'units': elementset.start.units,
                                            'x': compose_start[0] + elementset.start.x,
                                            'y': compose_start[1] + elementset.start.y,
                                        },
                                        'cover': elementset.cover,
                                    })
                                )
                        
                    if elementset_key == 'tiles':
                        decomposition[0] = buffer_sets
                    elif elementset_key == 'struts':
                        decomposition[1] = buffer_sets
                    elif elementset_key == 'plates':
                        decomposition[2] = buffer_sets
    
    return (decomposition[0], decomposition[1], decomposition[2])


def _init_jit():
    log.debug('Initializing JIT functions...', '_init_jit')

    screen_crop_box(
        (1,2),
        (1,2),
        (1,2)
    )
    on_screen(
        (0,1),
        (0,1,2,3), 
        (1,2), 
        (1,2)
    )
    tile_coordinates(
        (1,2),
        (1,2),
        (1,2)
    )
    slot_avatar_coordinates(
        (('slash','sword'),),
        (('sword',10,10),),
        (('item',10,10),),
        ((1,2),),
        ((1,2),(3,4),),
        ((1,2),(3,4),),
        ('slash'),
        (('slash',1),),
        'item',
        'arrow',
        (1,2),
        (3,4),
        (5,6)
    )
    mirror_coordinates(
        (1,2),
        'right',
        'top',
        'vertical',
        (1,2),
        (1,2),
        (1,2),
        (1,2)
    )
    decompose_animate_stature('test_state')

_init_jit()