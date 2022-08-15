from typing import Union

import munch

import onta.settings as settings
import onta.util.logger as logger

import onta.engine.noumena.substrata as substrata
import onta.engine.static.calculator as calculator


log = logger.Logger('onta.engine.collisions', settings.LOG_LEVEL)


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


def calculate_blunt_attackbox(
    sprite: munch.Munch,
    directional_atkboxes: munch.Munch
) -> tuple:
    """Calculate the attack hitbox for an _Equpiment Apparel_ of type `blunt` based on the direction and current frame of the provided _Sprite_.

    :param sprite: _description_
    :type sprite: munch.Munch
    :param attack_props: _description_
    :type attack_props: munch.Munch
    :return: The current attackbox for an _Sprite_ engaged in combat. **NOTE**: If the _Sprite_ `frame` does not map to any frames of the _Equipment_, i.e. the animation has not yet gotten to the point where an attackbox exists, this method will return `None`
    :rtype: tuple
    """
    atkbox_frames = [ 
        directed_box 
        for directed_box
        in directional_atkboxes.get(sprite.stature.direction)
        if directed_box.frame == sprite.frame
    ]
    if atkbox_frames:
        atkbox = atkbox_frames.pop()
        return  (
            int(sprite.position.x + atkbox.offset.x),
            int(sprite.position.y + atkbox.offset.y),
            atkbox.size.w,
            atkbox.size.h
        )
    return None


def calculate_projectile_attackbox(
    sprite: munch.Munch,
    directional_atkboxes: munch.Munch,
) -> tuple:
    """Calculate the attack hitbox for an _Equpiment Apparel_ of type `blunt` based on the direction of the provided _Sprite_.

    :param sprite: _description_
    :type sprite: munch.Munch
    :param attack_props: _description_
    :type attack_props: munch.Munch
    :return: _description_
    :rtype: tuple
    """
    raw_atkbox = directional_atkboxes.get(sprite.stature.direction)

    if raw_atkbox is None:
        return raw_atkbox

    format_atkbox = (
        int(sprite.position.x + raw_atkbox.offset.x),
        int(sprite.position.y + raw_atkbox.offset.y),
        raw_atkbox.size.w,
        raw_atkbox.size.h
    )
    return format_atkbox


def collision_set_relative_to(
    hitbox_key: str,
    npc_hitboxes: munch.Munch,
    strut_hitboxes: munch.Munch, # strutsets.get(layer_key).hitboxes
    container_hitboxes: munch.Munch, # platesets.get(layer_key).containeers
    gates: munch.Munch, #  self.get_typed_platesets(layer_key, 'gate')
    switch_map: munch.Munch, # self.switch_map(layer)
) -> list:
    """Returns a list of the typed hitbox a given sprite can possibly collide with on a given layer. 

    :param sprite: _description_
    :type sprite: str
    :param sprite_key: _description_
    :type sprite_key: str
    :param hitbox_key: _description_
    :type hitbox_key: str
    :return: list of lists containing the possible collision hitboxes
    :rtype: list

    .. note::
        Doesn't add pressure, doors or masses to the collision set, as they are handled separately in the game loop.
    """

    collision_sets = []
    if hitbox_key == 'sprite' and \
        npc_hitboxes is not None:
        collision_sets += npc_hitboxes

    if hitbox_key == 'strut' and \
            strut_hitboxes is not None:
        collision_sets += strut_hitboxes

    if hitbox_key == 'strut' and \
        container_hitboxes is not None:
        collision_sets += [
            container.hitbox for container in container_hitboxes
        ]
        collision_sets += [ 
            gate.hitbox for gate in gates
            if not switch_map.get(gate.key).get(str(gate.index))
        ]
        # doesn't add pressures, doors or masses, as they are handled separately
    
    collision_sets = [
        box 
        for box in collision_sets 
        if box is not None 
        and None not in box
    ]
    return collision_sets


def detect_collision(
    object_hitbox: tuple, 
    hitbox_list: list
) -> Union[tuple, None]:
    """Determines if a sprite's hitbox has collided with a list of hitboxes

    :param object_key: 
    :type object_key: str
    :param object_hitbox: _description_
    :type object_hitbox: tuple
    :param hitbox_list: _description_
    :type hitbox_list_tuple: tuple
    :return: The hitbox with which the `object` collided, `None` otherwise
    :rtype: Union[tuple, None]

    .. note::
        This method assumes it only cares _if_ a collision occurs, not with _what_ the collision occurs. The hitbox list is traversed and if any one of the contained hitboxes intersects the sprite, `True` is returned. If none of the hitboxes in the list intersect the given sprite, `False` is returned.
    
    .. todo::
        Modify this to return the direction of the collision. Need to recoil sprite based on where the collision came from, not which direction the sprite is heading...
    """
    if not hitbox_list or None in hitbox_list:
        return None

    compile_result = calculator.any_intersections(
        object_hitbox,
        hitbox_list
    )

    # compiled version returns all -1 instead of None to avoid type-check problems
        # TODO: that was for numba, not cython
    if all(el == -1 for el in iter(compile_result)):
        return None

    return compile_result


def project(
    projectile: munch.Munch
) -> None:
    if projectile.direction == 'up':
        setattr(
            projectile,
            'current',
            (
                projectile.current[0], 
                projectile.current[1] - projectile.speed
            )
        )
    elif projectile.direction == 'left':
        setattr(
            projectile,
            'current',
            (
                projectile.current[0] - projectile.speed,
                projectile.current[1]
            )
        )
    elif projectile.direction == 'down':
        setattr(
            projectile,
            'current',
            (
                projectile.current[0],
                projectile.current[1] + projectile.speed
            )
        )
    elif projectile.direction == 'right':
        setattr(
            projectile,
            'current',
            (
                projectile.current[0] + projectile.speed,
                projectile.current[1]
            )
        )

    setattr(
        projectile,
        'attackbox',
        ( 
            projectile.current[0], 
            projectile.current[1], 
            projectile.attackbox[2],
            projectile.attackbox[3]
        )
    )


def recoil_sprite(
    sprite: munch.Munch, 
    sprite_dim: tuple,
    sprite_speed: munch.Munch,
    collision_box: tuple
) -> None:
    """Recoil a _Sprite_ based on the direction of its collision with the passed-in `collision_box`.

    :param sprite: _Sprite_ to be recoiled.
    :type sprite: munch.Munch
    :param sprite_dim:
    :type sprite_dim: tuple
    :param sprite_props: Properties for passed-in _Sprite_.
    :type sprite_props: munch.Munch
    :param collision_box: The hitbox off of which the _Sprite_ is recoiling.
    :type collision_box: tuple
    """
    sprite_box = (
        sprite.position.x, 
        sprite.position.y,
        sprite_dim[0],
        sprite_dim[1]
    )
    sprite_center = calculator.center(sprite_box)

    proj = calculator.projection(45)

    if sprite_center[0] < collision_box[0]:
        if sprite_center[1] > collision_box[1]+collision_box[3]:
            log.debug('Recoiling sprite to the bottom left', 'recoil_sprite')
            sprite.position.x -= proj[0] * sprite_speed
            sprite.position.y += proj[1] * sprite_speed
            return
        elif sprite_center[1] < collision_box[1]:
            log.debug('Recoiling sprite to the top left', 'recoil_sprite')
            sprite.position.x -= proj[0] * sprite_speed
            sprite.position.y -= proj[1] * sprite_speed
            return
        log.debug('Recoiling sprite to the left', 'recoil_sprite')
        sprite.position.x -= sprite_speed
        return

    elif sprite_center[0] > collision_box[0] + collision_box[2]:
        if sprite_center[1] > collision_box[1]+collision_box[3]:
            log.debug('Recoiling sprite to the bottom right', 'recoil_sprite')
            sprite.position.x += proj[0] * sprite_speed
            sprite.position.y += proj[1] * sprite_speed
            return
        elif sprite_center[1] < collision_box[1]:
            log.debug('Recoiling sprite to the top right', 'recoil_sprite')
            sprite.position.x += proj[0] * sprite_speed
            sprite.position.y -= proj[1] * sprite_speed
            return
        log.debug('Recoiling sprite to the right', 'recoil_sprite')
        sprite.position.x += proj[0] * sprite_speed
        return

    else: # the center
        if sprite_center[1] > collision_box[1]+collision_box[3]:
            log.debug('Recoiling sprite to the bottom', 'recoil_sprite')
            sprite.position.y += proj[1] * sprite_speed
            return
        log.debug('Recoiling sprite to the top', 'recoil_sprite')
        sprite.position.y -= proj[1] * sprite_speed
        return


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
    layer_pressures, 
    layer_switch_map,
    gates,
) -> None:
    for pressure in layer_pressures:

        if isinstance(hitbox, tuple):
            collision_box = detect_collision(
                pressure.hitbox, 
                [ hitbox ]
            )
        elif isinstance(hitbox, list):
            collision_box = detect_collision(
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
    sprite_props,
    platesets,
    plate_props,
    tile_dimensions,
) -> None:
    sprite_hitbox = substrata.sprite_hitbox(
        munch.unmunchify(sprite), 
        'sprite', 
        munch.unmunchify(sprite_props)
    )
    masses = platesets.get(sprite.layer).masses.copy()
    for mass in masses:
        collision_box = detect_collision(
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
                substrata.set_hitbox(
                    munch.unmunchify(plate_props.get(mass.key).hitbox.sprite),
                    munch.unmunchify(plate),
                    tile_dimensions
                )
            )
            setattr(
                plate.hitbox,
                'strut',
                substrata.set_hitbox(
                    munch.unmunchify(plate_props.get(mass.key).hitbox.strut),
                    munch.unmunchify(plate),
                    tile_dimensions
                )
            )