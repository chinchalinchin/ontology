from PIL import Image
import PySide6.QtGui as QtGui

from PIL.ImageQt import ImageQt

import onta.settings as settings


def convert_to_gui(cropped: Image.Image):
    qim = ImageQt(cropped)
    pix = QtGui.QPixmap.fromImage(qim)
    return pix


def new_image(dim: tuple) -> Image.Image:
    return Image.new(settings.IMG_MODE, dim, settings.IMG_BLANK)


def replace_alpha(img: Image.Image, alpha: int) -> None:
    return img.putalpha(alpha)


def channels(dim, channels):
    return Image.new(settings.IMG_MODE, dim, channels)

def int_tuple(tup: tuple) -> tuple:
    return (
        int(tup[0]), 
        int(tup[1])
    )