from typing import Callable
import munch

import onta.engine.instinct.impulse as impulse
import onta.engine.static.calculator as calculator

import onta.settings as settings

import onta.util.logger as logger

log = logger.Logger('onta.engine.instinct.abstract', settings.LOG_LEVEL)

def approach(
    sprite_key: str,
    sprite: munch.Munch,
    sprite_desire: munch.Munch,
    sprite_stature: munch.Munch,
    sprite_props: munch.Munch,
    sprites: munch.Munch,
    reorient_function: Callable[[str], str]
):
    # returns whether or not _ruminate should break!

    # ...if not currently fleeing
    if sprite.path is not None and 'flee' in sprite.path:
        return
    
    # ...or engaged in combat
    if sprite.stature.action in sprite_stature.decomposition.combat:
        return

    sprite_pos = (sprite.position.x, sprite.position.y)

    # ...then evaluate the conditions for approach
    for condition in sprite_desire.conditions:

        if condition.function == 'aware':

            desire_pos = impulse.locate_desire(
                sprite_desire.target,
                sprite,
                sprites,
            )
            distance = calculator.distance(
                desire_pos,
                sprite_pos
            )

            if distance <= sprite_props.radii.aware.approach:

                log.debug(
                    f'{sprite_key} aware of {sprite_desire.target} and approaching...',
                    'approach'
                )
                if sprite.path != sprite_desire.target:
                    sprite.path = sprite_desire.target
                new_direction = reorient_function(sprite_key)
                setattr(
                    sprite,
                    'intent',
                    munch.Munch({
                        'intention': 'move',
                        'action': 'walk',
                        'direction': new_direction,
                        'expression': sprite.stature.expression
                    })
                )
                setattr(sprite.memory, 'intent', None)
                return False

            elif distance > sprite_props.radii.aware.approach \
                    and sprite.path == sprite_desire.target:

                log.debug(
                    f'{sprite_key} unaware of {sprite_desire.target}...',
                    'approach'
                )
                setattr(sprite, 'path', None)
                setattr(sprite.memory, 'intent', None)
                

        elif condition.function == 'always':
            log.verbose(
                f'{sprite_key} always desires {sprite_desire.mode} {sprite_desire.target}...',
                'approach'
            )
            sprite.path = sprite_desire.target
            new_direction = reorient_function(sprite_key)
            setattr(
                sprite,
                'intent',
                munch.Munch({
                    'intention': 'move',
                    'action': 'walk',
                    'direction': new_direction,
                    'expression': sprite.stature.expression
                })
            )
            setattr(sprite.memory, 'intent', None)
            return True
    return False
