"""
# onta.engine.instinct.impulse

A module for transforming _Sprite_ `intent` into in-game action. 

.. note:: 
    * The functions in this module may alter the `position` of a _Sprite_, but they will never alter the `stature` of a _Sprite_.
"""

from typing import Union
import munch

import onta.settings as settings

import onta.engine.collisions as collisions
import onta.engine.static.calculator as calculator

import onta.util.logger as logger


log = logger.Logger('onta.world.instinct.impulses', settings.LOG_LEVEL)


def locate_desire(
    target,
    sprite,
    sprites, 
) -> Union[tuple, None]:
    # TODO: take into account sprite layer and target layer, will need to pass in sprite

    log.verbose(f'Searching for {target.path}', 'locate_desire')

    invert = True if target.path.split(' ')[0] == 'not' else False
        
    if target.path in list(sprites.keys()):
        log.verbose('Target is dynamic, retrieving sprite position...', 'locate_desire')
        if invert:
            return (
                sprite.position.x - sprites.get(target.path).position.x,
                sprite.position.y - sprites.get(target.path).position.y,

            )
        return (
            sprites.get(target.path).position.x, 
            sprites.get(target.path).position.y
        )
    elif sprite.path in list(sprite.memory.paths.keys()):
        log.verbose('Target is static, retrieving path...', 'locate_desire')
        if invert: 
            return (
                sprite.position.x - sprite.memory.paths.get(target.path).position.x,
                sprite.position.y - sprite.memory.paths.get(target.path).position.y,
            )
        return ( 
            sprite.memory.paths.get(target.path).x, 
            sprite.memory.paths.get(target.path).y
        )
    return None


def move(
    sprite: munch.Munch,
    sprite_props: munch.Munch
) -> None:
    
    if sprite.stature.action == 'run':
        speed = sprite_props.speed.run
    elif sprite.stature.action == 'walk':
        speed = sprite_props.speed.walk

    if sprite.stature.direction == 'up':
        sprite.position.y -= speed

    elif sprite.stature.direction  ==  'up_left':
        proj = calculator.projection()
        sprite.position.x -= speed*proj[0]
        sprite.position.y -= speed*proj[1]

    elif sprite.stature.direction == 'left':
       sprite.position.x -= speed

    elif sprite.stature.direction == 'down_left':
        proj = calculator.projection()
        sprite.position.x -= speed*proj[0]
        sprite.position.y += speed*proj[1]

    elif sprite.stature.direction == 'down':
        sprite.position.y += speed

    elif sprite.stature.direction == 'down_right':
        proj = calculator.projection()
        sprite.position.x += speed*proj[0]
        sprite.position.y += speed*proj[1]

    elif sprite.stature.direction == 'right':
        sprite.position.x += speed

    elif sprite.stature.direction == 'up_right':
        proj = calculator.projection()  
        sprite.position.x += speed*proj[0]
        sprite.position.y -= speed*proj[1]


def combat(
    sprite_key,
    sprite,
    sprites_props,
    sprite_dim,
    apparel_props,
    target_sprites,
    # will need to pass in `projectiles`
) -> None: 
    if any(action in sprite.stature.action for action in ['cast', 'shoot', 'slash', 'thrust']):
        equip_key = sprite.slots.get(sprite.stature.action)

        if equip_key is None:
            # NOTE: this means if sprite doesn't have equipment, they can't engage in combat.
            #           is that what you want ... ? what about good, ol' fashioned fisticuffs?
            return        
                    
        if apparel_props.equipment.get(equip_key).type == 'projectile':
            ammo_types = list(
                apparel_props.equipment.get(equip_key).properties.ammo.keys()
            )

            if sprite.packs.belt in ammo_types:
                # will need to somehow save when the arrow was fired, to calculate distance
                # world.projectiles = [{ key: key, index: index, max_distance: int, speed: int, current:tuple, origin: tuple}]
                #   where every iteration distance(current,origin)<max_distance to survive
                attack_box = collisions.calculate_projectile_attackbox(
                    sprite,
                    apparel_props.equipment.get(equip_key).properties.ammo.get(
                        sprite.packs.belt).attackbox
                )

        
        elif apparel_props.equipment.get(equip_key).type == 'blunt':

            attack_box = collisions.calculate_blunt_attackbox(
                sprite,
                apparel_props.equipment.get(equip_key).properties.attackboxes
            )

            if not attack_box:
                return

            for target_key, target in target_sprites.items():
                if target_key == sprite_key or target.layer != sprite.layer:
                    continue

                target_hitbox = collisions.calculate_sprite_hitbox(
                    target,
                    'attack',
                    sprites_props.get(target_key)
                )

                if not target_hitbox:
                    continue

                collision_box = collisions.detect_collision(
                    equip_key, 
                    attack_box, 
                    [ target_hitbox ]
                )

                if not collision_box:
                    continue

                collisions.recoil_sprite(
                    target,
                    sprite_dim,
                    apparel_props.equipment.get(equip_key).properties.collide,
                    attack_box
                )

                # if target not in combat
                setattr(
                    target.stature,
                    'expression',
                    'surprise'
                )
                # if target not focused on sprite
                setattr(
                    target.stature,
                    'attention',
                    sprite_key
                )

                
def express(
    sprite,
    sprite_props
) -> None:
    pass


# TODO: separate use from interact
def operate(
    sprite: munch.Munch,
    sprite_props: munch.Munch,
    platesets: munch.Munch, 
    plate_props: munch.Munch,
    switch_map: munch.Munch,
) -> None:

    sprite_hitbox = collisions.calculate_sprite_hitbox(
        sprite,
        'sprite',
        sprite_props
    )

    triggered = False

    for door in platesets.doors:
        if collisions.detect_collision(door.key, sprite_hitbox, [ door.hitbox ] ):
            sprite.layer = door.content
            triggered = True
            break

    if not triggered:
        for container in platesets.containers:
            key, index = container.key, container.index
            modified_hitbox = (
                container.position.x, 
                container.position.y,
                plate_props.get(key).size.w,
                plate_props.get(key).size.h    
            )
            if not switch_map.get(sprite.layer).get(key).get(index) and \
                collisions.detect_collision(key, sprite_hitbox,[ modified_hitbox ]):
                log.debug('Detected sprite container operation', 'operate')
                setattr(
                    switch_map.get(sprite.layer).get(key),
                    str(index),
                    True
                )
                triggered = True

                # TODO: deliver item to sprite via content
                break


