from PIL import Image
import PySide6.QtGui as QtGui

from PIL.ImageQt import ImageQt

import onta.settings as settings


def convert_to_gui(cropped: Image.Image):
    return QtGui.QPixmap.fromImage(ImageQt(cropped))


def open_image(
    path:str
) -> Image.Image:
    return Image.open(path).convert(settings.IMG_MODE)


def new_image(
    dim: tuple
) -> Image.Image:
    return Image.new(settings.IMG_MODE, dim, settings.IMG_BLANK)


def replace_alpha(
    img: Image.Image, 
    alpha: int
) -> None:
    return img.putalpha(alpha)


def channels(dim, channels):
    return Image.new(settings.IMG_MODE, dim, channels)

def int_tuple(tup: tuple) -> tuple:
    return ( int(tup[0]), int(tup[1]))