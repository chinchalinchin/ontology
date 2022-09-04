import functools
import munch
from collections \
    import OrderedDict
from PIL \
    import Image
from PIL.ImageQt \
    import ImageQt
from PySide6 \
    import QtGui

from onta.metaphysics \
    import settings


def render_paste(
    canvas: Image.Image,
    frame: Image.Image,
    coordinates: tuple
) -> None:
    return canvas.paste(
        frame,
        coordinates,
        frame
    )


def render_composite(
    canvas: Image.Image,
    frame: Image.Image,
    coordinates: tuple
) -> None:
    return canvas.alpha_composite(
        frame, 
        coordinates 
    )


def convert_to_gui(
    cropped: Image.Image
) -> QtGui.QPixmap:
    return QtGui.QPixmap.fromImage(
        ImageQt(cropped)
    )


def open_image(
    path:str
) -> Image.Image:
    return Image.open(path).convert(settings.IMG_MODE)


def new_image(
    dim: tuple
) -> Image.Image:
    return Image.new(
        settings.IMG_MODE, 
        int_tuple(dim), 
        settings.IMG_BLANK
)


def replace_alpha(
    img: Image.Image, 
    alpha: int
) -> None:
    return img.putalpha(alpha)


@functools.lru_cache(maxsize=5)
def channels(
    dim: tuple, 
    channels: tuple
) -> Image.Image:
    return Image.new(
        settings.IMG_MODE, 
        int_tuple(dim), 
        channels
    )


def int_tuple(
    tup: tuple
) -> tuple:
    return ( 
        int(tup[0]), 
        int(tup[1]) 
    )


def order_sprite_dict(
    unordered_sprites: munch.Munch
) -> OrderedDict:
    # doesn't matter, as long as player is last
    ordered_sprites = OrderedDict({
        sprite_key: sprite 
        for sprite_key, sprite 
        in unordered_sprites.items()
        if sprite_key != 'hero'
    })
    ordered_sprites.update({
        'hero': unordered_sprites.get('hero')
    })
    return ordered_sprites


def order_render_dict(
    unordered_dict: munch.Munch
) -> OrderedDict:
    render_map = {}
    ordered_dict = OrderedDict()

    if len(unordered_dict) == 0:
        return OrderedDict({})

    render_map = { 
        val['order']: key 
        for key, val 
        in unordered_dict.items() 
    }

    ordered_map = list(render_map.keys())
    ordered_map.sort()

    for order in ordered_map:
        ordered_dict[render_map[order]] = \
            unordered_dict[render_map[order]]
    
    return ordered_dict