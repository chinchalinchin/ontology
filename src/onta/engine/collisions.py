from typing import Union

import munch


import onta.settings as settings
import onta.engine.static.calculator as calculator
import onta.util.logger as logger

log = logger.Logger('onta.engine.collisions', settings.LOG_LEVEL)


######################
### "STATIC" FUNCTIONS
######################

def generate_collision_map(
    npcs: munch.Munch
) -> munch.Munch:
    """_summary_

    :param npcs: _description_
    :type npcs: munch.Munch
    :return: _description_
    :rtype: munch.Munch
    """
    collision_map = munch.Munch({ 
        npc_1_key: munch.Munch({
            npc_2_key: False for npc_2_key in npcs.keys()
        }) for npc_1_key in npcs.keys()
    })
    return collision_map


def calculate_set_hitbox(
    set_hitbox: tuple, 
    set_conf: munch.Munch, 
    tile_dim: tuple
) -> Union[tuple, None]:
    """_summary_

    :param set_hitbox: _description_
    :type set_hitbox: tuple
    :param set_conf: _description_
    :type set_conf: munch.Munch
    :param tile_dim: _description_
    :type tile_dim: tuple
    :return: _description_
    :rtype: Union[tuple, None]
    """
    if set_hitbox:
        x,y = calculator.scale(
            ( set_conf.start.x, set_conf.start.y ),
            tile_dim,
            set_conf.start.units
        )
        hitbox = (
            x + set_hitbox.offset.x, 
            y + set_hitbox.offset.y,
            set_hitbox.size.w,
            set_hitbox.size.h
        )
        return hitbox
    return None


def calculate_sprite_hitbox(
        sprite: munch.Munch, 
        hitbox_key: str,
        sprite_props: munch.Munch
    ) -> Union[tuple, None]:
        """_summary_

        :param sprite: _description_
        :type sprite: munch.Munch
        :param hitbox_key: _description_
        :type hitbox_key: str
        :return: _description_
        :rtype: Union[tuple, None]

        .. note::
            A sprite's hitbox dimensions are fixed, but the actual hitbox coordinates depend on the position of the sprite. This method must be called each iteration of the world loop, so the newest coordinates of the hitbox are retrieved.
        """
        
        raw_hitbox = sprite_props.hitboxes.get(hitbox_key)
        calc_hitbox = (
            sprite.position.x + raw_hitbox.offset.x,
            sprite.position.y + raw_hitbox.offset.y,
            raw_hitbox.size.w,
            raw_hitbox.size.h
        )
        return calc_hitbox


def calculate_attackbox(
    sprite: munch.Munch,
    attack_props: munch.Munch
) -> tuple:
    # TODO:
    pass


def detect_collision(
    sprite_hitbox: tuple, 
    hitbox_list: list
) -> bool:
    """Determines if a sprite's hitbox has collided with a list of hitboxes

    :param sprite_hitbox: _description_
    :type sprite_hitbox: tuple
    :param hitbox_list: _description_
    :type hitbox_list: list
    :return: _description_
    :rtype: bool

    .. note::
        This method assumes it only cares _if_ a collision occurs, not with _what_ the collision occurs. The hitbox list is traversed and if any one of the contained hitboxes intersects the sprite, `True` is returned. If none of the hitboxes in the list intersect the given sprite, `False` is returned.
    
    .. todo::
        Modify this to return the direction of the collision. Need to recoil sprite based on where the collision came from, not which direction the sprite is heading...
    """

    for hitbox in hitbox_list:
        if hitbox and calculator.intersection(sprite_hitbox, hitbox):
            # NOTE: return true once collision is detected. it doesn't matter where it occurs, 
            #       only what direction the hero is travelling...
            # TODO: fix that!
            printable_hitbox = tuple(round(dim) for dim in sprite_hitbox)
            log.debug(
                f'Detected sprite hitbox {printable_hitbox} collision with hitbox at {hitbox}', 
                'detect_collision'
            )
            return hitbox
    return None


############################
### STATE ALTERING FUNCTIONS
############################


def recoil_sprite(
    sprite: munch.Munch, 
    sprite_dim: tuple,
    sprite_props: munch.Munch,
    collision_box: tuple
) -> None:
    """_summary_

    :param sprite: _description_
    :type sprite: munch.Munch
    :param sprite_props: _description_
    :type sprite_props: munch.Munch
    """
    sprite_box = (
        sprite.position.x, 
        sprite.position.y,
        sprite_dim[0],
        sprite_dim[1]
    )
    sprite_center = calculator.center(sprite_box)
    collision_center = calculator.center(collision_box)

    # the direction depends on the angle between the centers...


    if sprite.position.y > collision_box[1]:
        # above and to the left
        if sprite.position.x < collision_box[0]:
            return
        # above and to the right

        return
    # below and to the left
    elif sprite.position.x < collision_box[0]:
        return

    # below and to the right
    return


def recoil_plate(
    plate: munch.Munch, 
    sprite: munch.Munch, 
    sprite_dim: tuple,
    sprite_props: munch.Munch, 
    collision_box: tuple
) -> None:
    """_summary_

    :param plate: _description_
    :type plate: munch.Munch
    :param sprite: _description_
    :type sprite: munch.Munch
    :param sprite_props: _description_
    :type sprite_props: munch.Munch
    :param hero_flag: _description_
    :type hero_flag: bool
    """
    if 'down' in sprite.stature.direction:
        plate.start.y += sprite_props.speed.collide
    elif 'left' in sprite.stature.direction:
        plate.start.x -= sprite_props.speed.collide
    elif 'right' in sprite.stature.direction:
        plate.start.x += sprite_props.speed.collide
    else:
        plate.start.y -= sprite_props.speed.collide