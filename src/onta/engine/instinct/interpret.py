
import munch

def map_input_to_intent(
    hero: munch.Munch,
    sprite_stature: munch.Munch,
    user_input: munch.Munch
) -> munch.Munch:
    # current values
    hero.stature.action
    # will need direction if user input is a singular intent (use, interact, guard)
    hero.stature.direction
    hero.stature.emotion

    # only one direction can be enabled at a time, so this is equivalent to finding the direction
    enabled_direction = [
        direction for direction, flag in user_input.items() 
        if flag and direction in sprite_stature.decomposition.directions
    ]
    # only one action can be enabled at a time, so this is equivalent to finding the action
    enabled_action = [ 
        action for action, flag in user_input.items()
        if flag and action in sprite_stature.decomposition.actions
    ]
    # only one emotion can be enabled at a time, so this is equivalent to finding the action
    enabled_expressions = [
        expression for expression, flag in user_input.items()
        if flag and expression in sprite_stature.decomposition.expressions
    ]

    intention, action = None, None
    direction, expression = None, None

    # evaluate action flag first since they take precedence
        # Possible TODO: can this information be extracted from state or config?

    # Another possible TODO: can these maps that follow, from input to intention, be specified through 
        # configuration instead of hardcoded?
    if enabled_action:
        action = enabled_action.pop()
        direction = hero.stature.direction
        if user_input.use or user_input.interact:
            intention = 'operate'
        elif user_input.slash or user_input.thrust or user_input.shoot or \
            user_input.cast or user_input.guard:
            intention = 'combat'

    elif enabled_direction:
        intention = 'move'
        action = 'walk' if not user_input.sprint else 'sprint'
        direction = enabled_direction.pop()
        expression = hero.statue.expression

    if enabled_expressions:
        expression = enabled_expressions.pop()
    else:
        expression = hero.statue.expression


    return munch.Munch({
        'intention': intention,
        'action': action,
        'direction': direction,
        'expression': expression
    })