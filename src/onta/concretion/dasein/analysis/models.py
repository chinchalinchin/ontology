import onta.world as world


def stature_map(game_world: world.World):
    stature_keys = list(
        game_world.sprite_stature.keys()
    )
    return {
        stature_key: i 
        for i, stature_key 
        in enumerate(stature_keys)
    }


def predict(game_world: world.World):
    """
    
    .. note::
        ```python
        coefficients = [
            {
                'sprite_key': str,
                'value': float
            },
            # ...
        ]
        ```
    """
    prediction, smap, coefficients = \
        0, stature_map(game_world), model()

    for coefficient in coefficients:
        if coefficient['sprite_key'] != 'constant':
            sprite = game_world.get_sprite(
                coefficient['sprite_key']
            )

            mapped_stature = smap[
                sprite['state']
            ]

            contribution = mapped_stature * coefficient
        else:
            contribution = coefficient

        prediction += contribution

    return prediction

def model():
    pass
