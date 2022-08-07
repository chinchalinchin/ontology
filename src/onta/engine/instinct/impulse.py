from typing import Union
import munch

import onta.settings as settings

import onta.engine.collisions as collisions
import onta.engine.static.calculator as calculator
import onta.engine.static.formulae as formulae

import onta.util.logger as logger


log = logger.Logger('onta.world.instinct.impulses', settings.LOG_LEVEL)


def locate_desire(
    target, 
    sprites, 
    paths
) -> Union[tuple, None]:
    # TODO: take into account sprite layer and target layer, will need to pass in sprite
    log.verbose(f'Searching for {target}', 'locate_desire')

    if target in list(sprites.keys()):
        log.verbose('Target is dynamic, retrieving sprite position...', 'locate_desire')
        return (
            sprites.get(target).position.x, 
            sprites.get(target).position.y
        )
    elif target in list(paths.keys()):
        log.verbose('Target is static, retrieving path...', 'locate_desire')
        return ( paths.get(target).x, paths.get(target).y)
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
    sprite,
    sprite_props,
    apparel_stature
) -> None: 
    # will probably need more input here for other sprites, combat attack boxes, etc...
    if any(action in sprite.stature.action for action in ['cast', 'shoot', 'slash', 'thrust']):
        equip_key = sprite.slots.get(sprite.stature.action)

        if equip_key is None:
            return        
            
        attack_box = None
        if apparel_stature.equipment.get(equip_key).type == 'projectile':
            ammo_types = list(
                apparel_stature.equipment.get(equip_key).properties.ammo.keys()
            )
            if sprite.packs.belt in ammo_types:
                attack_box = collisions.calculate_attackbox(
                    sprite,
                    apparel_stature.equipment.get(equip_key).properties.ammo.get(
                        sprite.packs.belt).attackbox
                )
        elif apparel_stature.equipment.get(equip_key).type == 'blunt':
            attack_box = collisions.calculate_attackbox(
                sprite,
                apparel_stature.equipment.get(equip_key).properties.attackboxes
            )

def express(
    sprite,
    sprite_props
) -> None:
    pass

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


