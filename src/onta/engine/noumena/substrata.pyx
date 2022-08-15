from typing import Union
import onta.engine.static.calculator as calculator


def set_hitbox(
    hitbox: dict,
    set_conf: dict,
    tile_dim: tuple
):
    if hitbox:
        x,y = calculator.scale(
            ( set_conf['start']['x'], set_conf['start']['y'] ),
            tile_dim,
            set_conf['start']['units']
        )
        calc_box = (
            int(x + hitbox['offset']['x']), 
            int(y + hitbox['offset']['y']),
            hitbox['size']['w'],
            hitbox['size']['h']
        )
        return calc_box
    return None


def stationary_hitboxes(
    layers: list,
    tile_dimensions: tuple,
    strutsets: dict,
    platesets: dict,
    strut_props: dict,
    plate_props: dict
):
    for layer in layers:
        for static_set in ['strutset', 'plateset']:

            if static_set == 'strutset':
                iter_set = strutsets[layer].copy()
                props = strut_props
            else: # plateset
                iter_set = platesets[layer].copy()
                props = plate_props

            
            for set_key, set_conf in iter_set.items():
            
                for i, set_conf in enumerate(set_conf['sets']):

                    if props[set_key].get('type') == 'mass':
                        set_sprite_hitbox = set_hitbox(
                            props[set_key]['hitbox']['sprite'],
                            set_conf,
                            tile_dimensions
                        )
                        set_strut_hitbox = set_hitbox(
                            props[set_key]['hitbox']['strut'],
                            set_conf,
                            tile_dimensions
                        )
                        platesets[layer][set_key]['sets'][i]['hitbox'] = {
                            'sprite': set_sprite_hitbox,
                            'strut': set_strut_hitbox
                        }
                        continue

                    this_hitbox = set_hitbox(
                        props[set_key]['hitbox'],
                        set_conf,
                        tile_dimensions
                    )
                    if static_set == 'strutset':
                        strutsets[layer][set_key]['sets'][i]['hitbox'] = this_hitbox
                        continue

                    platesets[layer][set_key]['sets'][i]['hitbox'] = this_hitbox   
    return strutsets, platesets


def strut_hitboxes(
    strutsets: dict
) -> list:
    """_summary_

    :param layer: _description_
    :type layer: str
    :return: _description_
    :rtype: list
    """
    strut_hitboxes = []
    for strutset in strutsets.values():
        strut_hitboxes += [
            strut['hitbox'] for strut in strutset['sets']
        ]
    return strut_hitboxes


def sprite_hitbox(
    sprite: dict, 
    hitbox_key: str,
    sprite_props: dict
) -> Union[tuple, None]:
        """_summary_

        :param sprite: _description_
        :type sprite: munch.Munch
        :param hitbox_key: _description_
        :type hitbox_key: str
        :return: _description_
        :rtype: Union[tuple, None]

        .. note::
            A sprite's hitbox dimensions are fixed, but the actual hitbox coordinates depend on the position of the sprite. This method must be called each iteration of the world loop, so the newest coordinates of the hitbox are retrieved.
        """
        
        raw_hitbox = sprite_props['hitboxes'].get(hitbox_key)
        if raw_hitbox is None:
            return raw_hitbox
        calc_hitbox = (
            int(sprite['position']['x'] + raw_hitbox['offset']['x']),
            int(sprite['position']['y'] + raw_hitbox['offset']['y']),
            raw_hitbox['size']['w'],
            raw_hitbox['size']['h']
        )
        return calc_hitbox


def sprite_hitboxes(
    sprites: dict, 
    sprites_props: dict,
    hitbox_key: str,
    exclude: list = None
) -> list:
    """_summary_

    :param hitbox_key: _description_
    :type hitbox_key: str
    :param layer: _description_
    :type layer: str
    :param exclude: _description_, defaults to None
    :type exclude: list, optional
    :return: _description_
    :rtype: list
    """
    return [
        sprite_hitbox(
            sprite,
            hitbox_key, 
            sprites_props[sprite_key]
        ) for sprite_key, sprite in sprites.items()
        if exclude is None or sprite_key not in exclude
    ]