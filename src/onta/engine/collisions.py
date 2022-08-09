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


def calculate_blunt_attackbox(
    sprite: munch.Munch,
    directional_atkboxes: munch.Munch
) -> tuple:
    """Calculate the attack hitbox for an _Equpiment Apparel_ of type `blunt` based on the direction of the provided _Sprite_.

    :param sprite: _description_
    :type sprite: munch.Munch
    :param attack_props: _description_
    :type attack_props: munch.Munch
    :return: _description_
    :rtype: tuple
    """
    atkbox_frames = [ 
        directed_box 
        for directed_box
        in directional_atkboxes.get(sprite.stature.direction)
        if directed_box.frame == sprite.frame
    ]
    if atkbox_frames:
        atkbox =atkbox_frames.pop()
        return  (
            sprite.position.x + atkbox.offset.x,
            sprite.position.y + atkbox.offset.y,
            atkbox.size.w,
            atkbox.size.h
        )
    return None


def calculate_projectile_attackbox(
    sprite: munch.Munch,
    directional_atkboxes: munch.Munch
) -> tuple:
    """Calculate the attack hitbox for an _Equpiment Apparel_ of type `blunt` based on the direction of the provided _Sprite_.

    :param sprite: _description_
    :type sprite: munch.Munch
    :param attack_props: _description_
    :type attack_props: munch.Munch
    :return: _description_
    :rtype: tuple
    """
    atkboxes = directional_atkboxes.get(sprite.stature.direction)
    pass


def detect_collision(
    object_key: str,
    object_hitbox: tuple, 
    hitbox_list: list
) -> bool:
    """Determines if a sprite's hitbox has collided with a list of hitboxes

    :param object_key: 
    :type object_key: str
    :param object_hitbox: _description_
    :type object_hitbox: tuple
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
        if hitbox and calculator.intersection(object_hitbox, hitbox):
            printbox = tuple(round(dim) for dim in object_hitbox)
            printbox_dos = tuple(round(dim) for dim in hitbox)
            log.debug(
                f'Detected {object_key} hitbox {printbox} collision with hitbox at {printbox_dos}', 
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
    speed = sprite_props.speed.collide

    angle = calculator.angle_relative_to_center(sprite_center, collision_center)
    proj = calculator.projection()


    if sprite_center[0] < collision_box[0]:
        if sprite_center[1] > collision_box[1]+collision_box[3]:
            # from below and the left
            sprite.position.x -= proj[0] * speed
            sprite.position.y += proj[1] * speed
            return
        elif sprite_center[1] < collision_box[1]:
            # from above and the left
            sprite.position.x -= proj[0] * speed
            sprite.position.y -= proj[1] * speed
            return
        # from the left
        sprite.position.x -= speed
        return

    elif sprite_center[0] > collision_box[0] + collision_box[2]:
        if sprite_center[1] > collision_box[1]+collision_box[3]:
            # from below and the right
            sprite.position.x += proj[0] * speed
            sprite.position.y += proj[1] * speed
            return
        elif sprite_center[1] < collision_box[1]:
            # from above and the right
            sprite.position.x += proj[0] * speed
            sprite.position.y -= proj[1] * speed
            return
        # from the right
        sprite.position.x += proj[0] * speed
        return

    else: # the center
        if sprite_center[1] > collision_box[1]+collision_box[3]:
            # from below
            sprite.position.y += proj[1] * speed
            return
        # from above
        sprite.position.y -= proj[1] * speed
        return


    # ANGLE BASED DETECTION
    # think about what happens if sprite collides with large object.
    # large object eclipses sprite, and causes sprite to move in direction 
    # that doesn't look right. the angle is not the way to do this...
    # has to be done with coordinates, case by case.
    
    # if angle >= 337.5 or (angle >= 0 and angle<22.5):
    #     sprite.position.x += sprite_props.speed.collide

    # elif angle >= 22.5 and angle < 67.5:
    #     sprite.position.x += sprite_props.speed.collide * proj[0]
    #     sprite.position.y += sprite_props.speed.collide * proj[1]

    # elif angle >= 67.5 and angle < 112.5:
    #     sprite.position.y += sprite_props.speed.collide

    # elif angle >= 112.5 and angle < 157.5:
    #     sprite.position.x -= sprite_props.speed.collide * proj[0]
    #     sprite.position.y += sprite_props.speed.collide * proj[1]

    # elif angle >= 157.5 and angle < 202.5:
    #     sprite.position.x -= sprite_props.speed.collide

    # elif angle >= 202.5 and angle < 247.5:
    #     sprite.position.x -= sprite_props.speed.collide * proj[0]
    #     sprite.position.y -= sprite_props.speed.collide * proj[1]

    # elif angle >= 247.5 and angle < 292.5:
    #     sprite.position.y -= sprite_props.speed.collide

    # elif angle >= 292.5 and angle < 337.5:
    #     sprite.position.y -= sprite_props.speed.collide * proj[0]
    #     sprite.position.x += sprite_props.speed.collide * proj[1]


def recoil_plate(
    plate: munch.Munch, 
    sprite: munch.Munch, 
    sprite_props: munch.Munch, 
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


def detect_layer_pressure(
    hitbox,
    layer_pressures, # self.platesets.get(layer).pressures
    layer_switch_map, #self.switch_map.get(layer)
    gates, # self.get_typed_platesets(layer, 'gate') ## HOWEVER, this would presume gates 
    # can only be connected to plates on same layer. needs gates from ALL layers.
) -> None:
    for pressure in layer_pressures:
        if isinstance(hitbox, tuple):
            collision_box = detect_collision(
                pressure.key, 
                pressure.hitbox, 
                [ hitbox ]
            )
        elif isinstance(hitbox, list):
            collision_box = detect_collision(
                pressure.key, 
                pressure.hitbox, 
                hitbox
            )
        else:
            raise ValueError('Hitbox is not of type tuple or list')

        if collision_box and \
            not layer_switch_map.get(pressure.key).get(str(pressure.index)):
            log.debug(f'Switching pressure plate {pressure.key} on', '_physics')
            setattr(
                layer_switch_map.get(pressure.key),
                str(pressure.index),
                True
            )
            connected_gate = [
                munch.Munch({'key': gate.key, 'index': gate.index})
                for gate in gates
                if gate.content == pressure.content 
            ]
            if not connected_gate:
                continue
            connection = connected_gate.pop()
            setattr(
                layer_switch_map.get(connection.key),
                str(connection.index),
                True
            )

        elif not collision_box and \
            layer_switch_map.get(pressure.key).get(str(pressure.index)):
            log.debug(f'Switching pressure plate {pressure.key} off', '_physics')
            setattr(
                layer_switch_map.get(pressure.key),
                str(pressure.index),
                False
            )
            connected_gate = [
                munch.Munch({'key': gate.key, 'index': gate.index})
                for gate in gates
                if gate.content == pressure.content 
            ]
            if not connected_gate:
                continue
            connection = connected_gate.pop()
            setattr(
                layer_switch_map.get(connection.key),
                str(connection.index),
                False
            )


def detect_layer_sprite_to_mass_collision(

    sprite,
    sprite_props, #self.sprite_properties.get(sprite_key)
    platesets, # self.platesets
    plate_props, # self.plate_properties
    tile_dimensions,
) -> None:
    sprite_hitbox = calculate_sprite_hitbox(sprite, 'sprite', sprite_props)
    masses = platesets.get(sprite.layer).masses.copy()
    for mass in masses:
        collision_box = detect_collision(
            mass.key, 
            mass.hitbox.sprite, 
            [sprite_hitbox]
        )
        if collision_box:
            plate = platesets.get(sprite.layer).get(mass.key).sets[mass.index]
            recoil_plate(
                plate, 
                sprite,
                sprite_props,
            )
            setattr(
                plate.hitbox,
                'sprite',
                calculate_set_hitbox(
                    plate_props.get(mass.key).hitbox.sprite,
                    plate,
                    tile_dimensions
                )
            )
            setattr(
                plate.hitbox,
                'strut',
                calculate_set_hitbox(
                    plate_props.get(mass.key).hitbox.strut,
                    plate,
                    tile_dimensions
                )
            )