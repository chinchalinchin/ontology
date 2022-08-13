"""
# onta.engine.dasein.impulse

A module for transforming _Sprite_ `intent` into in-game action. 

.. note:: 
    * The functions in this module may alter the `position` of a _Sprite_, but they will never alter the `stature` of a _Sprite_. In certain cases, it may alter the `intent` of a _Sprite_ as well, as in the case of combat, when a sprite has to react next iteration.
"""

from typing import Union
import munch

import onta.settings as settings

import onta.engine.collisions as collisions
import onta.engine.static.calculator as calculator

import onta.util.logger as logger


log = logger.Logger('onta.engine.dasein.impulse', settings.LOG_LEVEL)


def locate_desire(
    target,
    sprite,
    sprites, 
) -> Union[tuple, None]:
    # TODO: take into account sprite layer and target layer, will need to pass in sprite

    log.verbose(f'Searching for {target}', 'locate_desire')

    flee = True if target.split(' ')[0] == 'flee' else False
    
    if flee:
        target = target.split(' ')[-1]

    if target in list(sprites.keys()):
        log.verbose('Target is dynamic, retrieving sprite position...', 'locate_desire')
        if flee:
            return (
                2*sprite.position.x - sprites.get(target).position.x,
                2*sprite.position.y - sprites.get(target).position.y,

            )
        return (
            sprites.get(target).position.x, 
            sprites.get(target).position.y
        )
    elif target in list(sprite.memory.paths.keys()):
        log.verbose('Target is static, retrieving path...', 'locate_desire')
        if flee: 
            return (
                2*sprite.position.x - sprite.memory.paths.get(target).x,
                2*sprite.position.y - sprite.memory.paths.get(target).y
            )
        return ( 
            sprite.memory.paths.get(target).x, 
            sprite.memory.paths.get(target).y
        )
    return None


def move(
    sprite: munch.Munch,
    sprite_props: munch.Munch
) -> None:
    
    if sprite.stature.action == 'run':
        speed = sprite_props.speed.run
    else:
        speed = sprite_props.speed.walk

    if sprite.stature.direction == 'up':
        sprite.position.y -= speed
        return

    elif sprite.stature.direction  ==  'up_left':
        proj = calculator.projection()
        sprite.position.x -= speed*proj[0]
        sprite.position.y -= speed*proj[1]
        return

    elif sprite.stature.direction == 'left':
       sprite.position.x -= speed
       return

    elif sprite.stature.direction == 'down_left':
        proj = calculator.projection()
        sprite.position.x -= speed*proj[0]
        sprite.position.y += speed*proj[1]

    elif sprite.stature.direction == 'down':
        sprite.position.y += speed
        return

    elif sprite.stature.direction == 'down_right':
        proj = calculator.projection()
        sprite.position.x += speed*proj[0]
        sprite.position.y += speed*proj[1]
        return

    elif sprite.stature.direction == 'right':
        sprite.position.x += speed

    elif sprite.stature.direction == 'up_right':
        proj = calculator.projection()  
        sprite.position.x += speed*proj[0]
        sprite.position.y -= speed*proj[1]
        return
    return


def combat(
    sprite_key: str,
    sprite: munch.Munch,
    sprite_stature: munch.Munch,
    sprites_props: munch.Munch,
    sprite_dim: tuple,
    apparel_props: munch.Munch,
    projectiles: list,
    projectile_props: munch.Munch,
    target_sprites: munch.Munch,
) -> None: 
    if any(action in sprite.stature.action 
            for action in sprite_stature.decomposition.combat):
        equip_key = sprite.slots.get(sprite.stature.action)

        if equip_key is None:
            # NOTE: this means if sprite doesn't have equipment, they can't engage in combat.
            #           is that what you want ... ? what about good, ol' fashioned fisticuffs?
            return        
                    
        if apparel_props.equipment.get(equip_key).type == 'projectile':

            if sprite.packs.belt in apparel_props.equipment.get(equip_key).properties.ammo and \
                sprite.frame == apparel_props.equipment.get(equip_key).properties.release:

                atkbox = collisions.calculate_projectile_attackbox(
                    sprite,
                    projectile_props.get(sprite.packs.belt).attackboxes
                )
                projectiles.append(
                    munch.Munch({
                        'key': sprite.packs.belt,
                        'layer': sprite.layer,
                        'direction': sprite.stature.direction,
                        'speed': projectile_props.get(sprite.packs.belt).speed,
                        'distance': projectile_props.get(sprite.packs.belt).distance,
                        'origin': ( atkbox[0], atkbox[1] ),
                        'current': ( atkbox[0], atkbox[1] ),
                        'attackbox': atkbox
                    })
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

                # if target not in combat or otherwise aware of hero
                if not any(
                    action in target.stature.action 
                    for action in sprite_stature.decomposition.combat
                ) or (
                    target.get('path') and \
                        sprite_key not in target.path
                ) or (
                    target.stature.get('attention') and \
                        sprite_key not in target.stature.attention
                ):
                    expression = 'surprise'
                else:
                    expression = 'anger'

                # however, what is player attacks friendly sprite
                # that is already focused on player?
                # then sprite will be aware and not in combat, but 
                # should nevertheless be surprised.

                if not target.stature.get('attention') or \
                    target.stature.attention != sprite_key:
                    attention = sprite_key
                else:
                    attention = target.stature.attention

                setattr(
                    target,
                    'intent',
                    munch.Munch({
                        'intention': target.stature.intention,
                        'action': target.stature.action,
                        'direction': target.stature.direction,
                        'expression': expression,
                        'attention': attention,
                        'disposition': target.stature.disposition
                    })
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
        if collisions.detect_collision(
            sprite_hitbox, 
            [ door.hitbox ]
        ):
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
                collisions.detect_collision(
                    sprite_hitbox, 
                    [ modified_hitbox ]
                ):
                log.debug('Detected sprite container operation', 'operate')
                setattr(
                    switch_map.get(sprite.layer).get(key),
                    str(index),
                    True
                )
                triggered = True

                # TODO: deliver item to sprite via content
                break


