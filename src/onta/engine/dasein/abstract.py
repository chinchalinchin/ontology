"""_summary_

The goal of this module is to map _Sprite_ `desires` to a _Sprite_ `intent`. Each function in this module will alter and update a _Sprite_ `intent` based on the `conditions` of its `desires`. 

.. warning:: 
    Beyond altering a _Sprite_ `intent` and `memory.intent`, these functions should not alter any direct state field. The point of this module is set to construct the message in the form of an `intent` the _World_ will process into a state field transformations.
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
    if sprite.stature.attention is not None and \
        'flee' in sprite.stature.attention:
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

                new_expression = None
                if sprite.stature.disposition == 'friendly':
                    new_expression = 'joy'

                elif sprite.stature.disposition == 'aggressive':
                    new_expression =  'hate'


                new_direction = reorient_function(sprite_key, sprite_desire.target)
                setattr(
                    sprite,
                    'intent',
                    munch.Munch({
                        'intention': 'move',
                        'action': 'walk',
                        'direction': new_direction,
                        'expression': new_expression,
                        'attention': sprite_desire.target,
                        'disposition': sprite.stature.disposition
                    })
                )
                setattr(sprite.memory, 'intent', sprite.stature)
                return 'break'
                

        elif condition.function == 'always':
            log.verbose(
                f'{sprite_key} always desires {sprite_desire.mode} {sprite_desire.target}...',
                'approach'
            )
            # i don't like that desires are acting directly on state here. it shoudl go through
            # intent, specifcally the attention property...

            # but, in order to call the reorient function, the path has to be set...
            new_direction = reorient_function(sprite_key, sprite_desire.target)
            setattr(
                sprite,
                'intent',
                munch.Munch({
                    'intention': 'move',
                    'action': 'walk',
                    'direction': new_direction,
                    'expression': sprite.stature.expression,
                    'attention': sprite_desire.target,
                    'disposition': sprite.stature.disposition
                })
            )
            setattr(sprite.memory, 'intent', sprite.stature)
            return 'break'
    return 'continue'


def attempt_unapproach(
    sprite_key,
    sprite,
    sprite_props,
    sprite_desire,
    sprites
) -> Literal['continue']:
    sprite_pos = (sprite.position.x, sprite.position.y)

    desire_pos = impulse.locate_desire(
        sprite_desire.target,
        sprite,
        sprites,
    )
    distance = calculator.distance(
        desire_pos,
        sprite_pos
    )
    always_flag = any(
        condition.function == 'always'
        for condition in
        sprite_desire.conditions
    )

    if distance > sprite_props.radii.aware.approach \
        and sprite.stature.attention == sprite_desire.target \
        and not always_flag:

        log.debug(
            f'{sprite_key} unaware of {sprite_desire.target}...',
            'approach'
        )
        if sprite.memory.intent and \
            sprite.memory.intent.get('attention') and \
            sprite.memory.intent.attention != sprite.intent.attention:
            setattr(sprite, 'intent', sprite.memory.intent)
            setattr(sprite.memory, 'intent', None)
        else:
            setattr(sprite, 'intent', None)

    return "continue"


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
                            # TODO: action calculation
                        'action': 'slash',
                        'direction': sprite.stature.direction,
                        'expression': sprite.stature.expression,
                        'attention': sprite_desire.target,
                        'disposition': sprite.stature.disposition
                    })
                )
                return 'break'
    return 'continue'


def attempt_unengage(
    sprite_key,
    sprite,
    sprite_props,
    sprite_desire,
    sprites,
) -> Literal['continue']:
    sprite_pos = (sprite.position.x, sprite.position.y)

    desire_pos = impulse.locate_desire(
        sprite_desire.target,
        sprite,
        sprites,
    )
    distance = calculator.distance(
        desire_pos,
        sprite_pos
    )
    if distance > sprite_props.radii.aware.engage :
        # need to compare sprite_desire.target to sprite.stature.attention
        log.verbose(
            f'{sprite_key} unaware of {sprite_desire.target}, so not engaging...',
            'attempt_unengage'
        )
        if sprite.memory.intent:
            setattr(sprite, 'intent', sprite.memory.intent)
            setattr(sprite.intent, 'expression', None)
        else:
            setattr(sprite, 'intent', None)

        setattr(sprite.memory, 'intent', None)
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

            if 'flee' not in sprite.stature.attention:
                log.debug(
                    f'{sprite_key} expression is {condition.value}, fleeing {sprite_desire.target}...',
                    'flee'
                )

                target = f'flee {sprite.stature.attention}' \
                    if sprite_desire.target == 'attention' else f'flee {sprite_desire.target}'

                new_direction = reorient_function(sprite_key, target)
                setattr(
                    sprite,
                    'intent',
                    munch.Munch({
                        'intention': 'move',
                        'action': 'run',
                        'direction': new_direction,
                        'expression': sprite.stature.expression,
                        'disposition': sprite.stature.disposition,
                        'attention': target
                    })
                )
                setattr(sprite.memory, 'intent', sprite.stature)
                
            return 'break'
    
    return 'continue'


def attempt_unflee(
    sprite_key: str,
    sprite: munch.Munch,
    sprite_props: munch.Munch,
    sprites: munch.Munch,
    reorient_function: Callable[[str], str]
) -> Literal['continue']:
    if 'flee' not in sprite.stature.attention:
        return 'continue'

    target_key = sprite.stature.attention.split(' ')[-1]
    target = sprites.get(target_key)

    distance = calculator.distance(
        (target.position.x, target.position.y),
        (sprite.position.x, sprite.position.y)
    )

    log.debug(
        f'{sprite_key} fleeing {target_key}, checking if safe...', 
        'attempt_unflee'
    )

    if distance > sprite_props.radii.aware.flee:
        log.debug(
            f'{sprite_key} lost sight of {target_key}, resetting stature...',
            'attempt-unflee'
        )

        
        target = list(sprite.memory.paths.keys())[-1]

        new_direction = reorient_function(sprite_key, target)
        setattr(
            sprite,
            'intent',
            munch.Munch({
                'intention': 'move',
                'action': 'walk',
                'direction': new_direction,
                'expression': None,
                'attention': target,
                'disposition': sprite.stature.disposition
            })
        )
    return 'continue'


### HELPERS

def remember(
    sprite_key: str,
    sprite: munch.Munch
) -> None:
    if not sprite.intent and \
        sprite.memory and \
        sprite.memory.intent and sprite.memory.intent.intention:
        
        log.verbose(
            f'{sprite_key} remembers {sprite.memory.intent.intention} intention',
            'remember'
        )
        setattr(sprite, 'intent', sprite.memory.intent)
        setattr(sprite.memory, 'intent', None)