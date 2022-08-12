"""_summary_

The goal of this module is to map _Sprite_ `desires` to a _Sprite_ `intent`. Each function in this module will alter and update a _Sprite_ `intent` based on the `conditions` of its `desires`.
"""

from typing import Callable, Literal, Union
import munch

import onta.engine.dasein.impulse as impulse
import onta.engine.static.calculator as calculator

import onta.settings as settings

import onta.util.logger as logger

log = logger.Logger('onta.engine.dasein.abstract', settings.LOG_LEVEL)


### RUMINATIONS

def approach(
    sprite_key: str,
    sprite: munch.Munch,
    sprite_desire: munch.Munch,
    sprite_stature: munch.Munch,
    sprite_props: munch.Munch,
    sprites: munch.Munch,
    reorient_function: Callable[[str], str]
) -> Union[Literal['continue'], Literal['break']]:
    # ...if currently fleeing
    if sprite.path is not None and 'flee' in sprite.path:
        return 'continue'
    
    # ...or in combat
    if sprite.stature.action in sprite_stature.decomposition.combat:
        return 'continue'

    sprite_pos = (sprite.position.x, sprite.position.y)

    # ...otherwise evaluate the conditions for approach
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
                return 'break'

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
            return 'break'
    return 'continue'


def engage(
    sprite_key: str,
    sprite: munch.Munch,
    sprite_desire: munch.Munch,
    sprite_stature: munch.Munch,
    sprite_props: munch.Munch,
    sprites: munch.Munch,
) -> Union[Literal['continue'], Literal['break']]: 
    if sprite.path is not None and 'flee' in sprite.path:
        return 'continue'

    sprite_pos = (sprite.position.x, sprite.position.y)

    for condition in sprite_desire.conditions:

        if condition.function == 'aware':
            log.infinite(
                f'{sprite_key} desires to engage {sprite_desire.target}', 
                'abstract'
            )
            desire_pos = impulse.locate_desire(
                sprite_desire.target,
                sprite,
                sprites,
            )
            distance = calculator.distance(
                desire_pos,
                sprite_pos
            )
            if distance <= sprite_props.radii.aware.engage and \
                sprite.stature.action not in sprite_stature.decomposition.combat:

                log.debug(
                    f'{sprite_key} aware of {sprite_desire.target} and engaging...',
                    '_ruminate'
                )
                # TODO: determine which slots are available for action
                setattr(sprite.memory, 'intent', sprite.stature)
                setattr(
                    sprite,
                    'intent',
                    munch.Munch({
                        'intention': 'combat',
                        # TODO: this
                        'action': 'slash',
                        'direction': sprite.stature.direction,
                        'expression': sprite.stature.expression
                    })
                )
                return 'break'
            elif distance > sprite_props.radii.aware.engage :
                log.verbose(
                    f'{sprite_key} unaware of {sprite_desire.target}, so not engaging...',
                    '_ruminate'
                )
                setattr(sprite, 'intent', None)
    return 'continue'


def flee(
    sprite_key,
    sprite,
    sprite_desire,
    reorient_function
) -> Union[Literal['continue'], Literal['break']]:
    for condition in sprite_desire.conditions:
        
        if condition.function == 'expression_equals' and \
            condition.value == sprite.stature.expression:

            setattr(sprite.memory, 'stature', sprite.stature)

            if 'flee' not in sprite.path:
                log.debug(
                    f'{sprite_key} expression is {condition.value}, fleeing {sprite_desire.target}...',
                    'flee'
                )

                sprite.path = f'flee {sprite.stature.attention}' \
                    if sprite_desire.target == 'attention' else f'flee {sprite_desire.target}'

                new_direction = reorient_function(sprite_key)
                setattr(
                    sprite,
                    'intent',
                    munch.Munch({
                        'intention': 'move',
                        'action': 'run',
                        'direction': new_direction,
                        'expression': sprite.stature.expression
                    })
                )
                setattr(sprite.memory, 'intent', None)
                
            return 'break'
    
    return 'continue'


def can_unflee(
    sprite_key: str,
    sprite: munch.Munch,
    sprite_props: munch.Munch,
    sprites: munch.Munch,
    reorient_function: Callable[[str], str]
) -> Union[Literal['continue'], Literal['break']]:
    if 'flee' not in sprite.path:
        return 'continue'

    target_key = sprite.path.split(' ')[-1]
    target = sprites.get(target_key)

    distance = calculator.distance(
        (target.position.x, target.position.y),
        (sprite.position.x, sprite.position.y)
    )

    log.debug(
        f'{sprite_key} fleeing {target_key}, checking if safe...', 
        'unflee'
    )

    if distance > sprite_props.radii.aware.flee:
        log.debug(
            f'{sprite_key} lost sight of {target_key}, resetting stature...',
            'unflee'
        )

        setattr(sprite, 'path', list(sprite.memory.paths.keys())[-1])
            # _reorient needs to be called after path is set
        new_direction = reorient_function(sprite_key)
        setattr(
            sprite,
            'intent',
            munch.Munch({
                'intention': 'move',
                'action': 'walk',
                'direction': new_direction,
                'expression': None
            })
        )
        setattr(sprite.memory, 'stature', None)
        setattr(sprite.memory, 'intent', None)
        return 'continue'
    return 'continue'


### HELPERS

def remember(
    sprite_key: str,
    sprite: munch.Munch
):
    if not sprite.intent and \
        sprite.memory and \
        sprite.memory.intent and sprite.memory.intent.intention:
        
        log.verbose(
            f'{sprite_key} remembers {sprite.memory.intent.intention} intention',
            'remember'
        )
        setattr(sprite, 'intent', sprite.memory.intent)
        setattr(sprite.memory, 'intent', None)