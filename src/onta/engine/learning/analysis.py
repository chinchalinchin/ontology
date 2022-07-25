import onta.world as world

# coefficients = [
#   {
#       'sprite_key': str,
#       'value': float
#   }
# ]

def state_map(game_world: world.World):
    state_keys = list(game_world.sprite_state_conf.keys())
    return {
        state_key: i for i, state_key in enumerate(state_keys)
    }

def predict(game_world: world.World):
    """
    
    .. notes:
        - coefficients example:
        ```python
        coefficients = [
            {
                'sprite_key': str,
                'value': float
            }
        ]
        ```
    """
    prediction, smap, coefficients = 0, state_map(game_world), model()
    for coefficient in coefficients:
        if coefficient['sprite_key'] != 'constant':
            sprite = game_world.get_sprite(coefficient['sprite_key'])
            mapped_state = smap[sprite['state']]
            contribution = mapped_state*coefficient
        else:
            contribution = coefficient
        prediction += contribution
    return prediction

def model():
    pass
