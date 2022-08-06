import munch

import onta.settings as settings

import onta.engine.collisions as collisions
import onta.engine.static.calculator as calculator
import onta.engine.static.formulae as formulae



def locate_desire(target, sprites, paths):
    # TODO: take into account sprite layer and target layer, will need to pass in sprite
    if target in list(sprites.keys()):
        return (
            sprites.get(target).position.x, 
            sprites.get(target).position.y
        )
    elif target in list(paths.keys()):
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
        sprite.stature.y -= speed

    elif sprite.stature.direction  ==  'up_left':
        proj = calculator.projection()
        sprite.position.x -= speed*proj[0]
        sprite.position.y -= speed*proj[1]

    elif sprite.stature.direction == 'left':
        pass

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
    if any(action in sprite.state for action in ['cast', 'shoot', 'slash', 'thrust']):
        act, direct = formulae.decompose_animate_stature(sprite.state) 
        equip_key = sprite.slots.get(act)            
        if equip_key is not None:
            attack_box = None
            if apparel_stature.equipment.get(equip_key).type == 'projectile':
                ammo_types = list(
                    apparel_stature.equipment.get(equip_key).properties.ammo.keys()
                )
                if sprite.packs.belt in ammo_types:
                    attack_box = collisions.calculate_attackbox(
                        sprite,
                        direct,
                        apparel_stature.equipment.get(equip_key).properties.ammo.get(
                            sprite.packs.belt).attackbox
                    )
            elif apparel_stature.equipment.get(equip_key).type == 'blunt':
                attack_box = collisions.calculate_attackbox(
                    sprite,
                    direct,
                    apparel_stature.equipment.get(equip_key).properties.attackbox
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
        if collisions.detect_collision(sprite_hitbox, [ door.hitbox ] ):
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
                collisions.detect_collision(sprite_hitbox,[ modified_hitbox ]):
                switch_map[sprite.layer][key][index] = True
                triggered = True

                # TODO: deliver item to sprite via content
                break


