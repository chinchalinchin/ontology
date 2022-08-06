
import munch

def map_input_to_intent(
    hero: munch.Munch,
    user_input: munch.Munch
) -> munch.Munch:
    # current values
    hero.stature.action
    # will need direction if user input is a singular intent (use, interact, guard)
    hero.stature.direction
    hero.stature.emotion

    intention = 'something'
    action = 'something'
    direction = 'something'
    emotion = 'something'
    return munch.Munch({
        'intention': intention,
        'action': action,
        'direction': direction,
        'emotion': emotion
    })