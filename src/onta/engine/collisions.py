from typing import Union
import onta.settings as settings
import onta.engine.calculator as calculator
import onta.util.logger as logger

log = logger.Logger('onta.engine.collisions', settings.LOG_LEVEL)


######################
### "STATIC" FUNCTIONS
######################

def generate_collision_map(
    npcs: dict
) -> dict:
    """_summary_

    :param npcs: _description_
    :type npcs: dict
    :return: _description_
    :rtype: dict
    """
    collision_map = { 
        npc_1_key: {
            npc_2_key: False for npc_2_key in npcs.keys()
        } for npc_1_key in npcs.keys()
    }
    return collision_map


def calculate_set_hitbox(
    set_hitbox: tuple, 
    set_conf: dict, 
    tile_dim: tuple
) -> Union[tuple, None]:
    """_summary_

    :param set_hitbox: _description_
    :type set_hitbox: tuple
    :param set_conf: _description_
    :type set_conf: dict
    :param tile_dim: _description_
    :type tile_dim: tuple
    :return: _description_
    :rtype: Union[tuple, None]
    """
    if set_hitbox:
        x,y = calculator.scale(
            (
                set_conf['start']['x'],
                set_conf['start']['y']
            ),
            tile_dim,
            set_conf['start']['units']
        )
        hitbox = (
            x + set_hitbox['offset']['x'], 
            y + set_hitbox['offset']['y'],
            set_hitbox['size']['w'],
            set_hitbox['size']['h']
        )
        return hitbox
    return None


def calculate_attackbox(

) -> tuple:
    # TODO:
    pass


def detect_collision(
    sprite_hitbox: tuple, 
    hitbox_list: list
) -> bool:
    """Determines if a sprite's hitbox has collided with a list of hitboxes

    :param sprite_hitbox: _description_
    :type sprite_hitbox: _type_
    :param hitbox_list: _description_
    :type hitbox_list: _type_
    :return: _description_
    :rtype: _type_

    .. note::
        This method assumes it only cares _if_ a collision occurs, not with _what_ the collision occurs. The hitbox list is traversed and if any one of the contained hitboxes intersects the sprite, `True` is returned. If none of the hitboxes in the list intersect the given sprite, `False` is returned.
    
    .. todo::
        Modify this to return the direction of the collision. Need to recoil sprite based on where the collision came from, not which direction the sprite is heading...
    """

    for hitbox in hitbox_list:
        if hitbox and \
            calculator.intersection(
                sprite_hitbox, 
                hitbox
            ):
            # NOTE: return true once collision is detected. it doesn't matter where it occurs, 
            #       only what direction the hero is travelling...
            log.verbose(f'Detected sprite hitbox {sprite_hitbox} collision with hitbox at {hitbox}', 
                'detect_collision')
            return True
    return False


############################
### STATE ALTERING FUNCTIONS
############################


def recoil_sprite(
    sprite: dict, 
    sprite_props: dict
) -> None:
    if 'down' in sprite['state']:
        sprite['position']['y'] -= sprite_props['collide']
    elif 'left' in sprite['state']:
        sprite['position']['x'] -= sprite_props['collide']
    elif 'right' in sprite['state']:
        sprite['position']['x'] += sprite_props['collide']
    else:
        sprite['position']['y'] += sprite_props['collide']

def recoil_plate(
    plate: dict, 
    sprite: dict, 
    sprite_props: dict, 
    hero_flag: bool
) -> None:
    """_summary_

    :param plate: _description_
    :type plate: _type_
    :param sprite: _description_
    :type sprite: _type_
    :param sprite_props: _description_
    :type sprite_props: _type_
    :param hero_flag: _description_
    :type hero_flag: _type_

    .. note::
        I am unsure where the mismatch between sprite left vs. hero right and sprite right vs. hero left comes from...I think it may have to do with the control mapping vs. the direction of the _(x,y)_ rendering plane, i.e. positive y is in the down direction...Until I discover the source of the error, this method needs an additional check when recoiling to left or right.
    """
    if 'down' in sprite['state']:
        plate['start']['y'] += sprite_props['collide']
    elif 'left' in sprite['state']:
        if hero_flag:
            plate['start']['x'] += sprite_props['collide']
        else:
            plate['start']['x'] -= sprite_props['collide']
    elif 'right' in sprite['state']:
        if hero_flag:
            plate['start']['x'] -= sprite_props['collide']
        else:
            plate['start']['x'] += sprite_props['collide']
    else:
        plate['start']['y'] -= sprite_props['collide']