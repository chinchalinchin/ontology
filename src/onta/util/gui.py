import io
from PIL import Image
import PySide6.QtGui as QtGui
import PySide6.QtCore as QtCore

import onta.settings as settings

def qimage_to_image(img: QtGui.QImage)-> Image.Image:
    buffer = QtCore.QBuffer()
    buffer.open(QtCore.QBuffer.ReadWrite)
    img.save(buffer, "PNG")
    pil_im = Image.open(io.BytesIO(buffer.data()))
    return pil_im

def new_image(dim: tuple) -> Image.Image:
    return Image.new(settings.IMG_MODE, dim, settings.IMG_BLANK)