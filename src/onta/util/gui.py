import io
from PIL import Image
import PySide6.QtGui as QtGui
import PySide6.QtCore as QtCore

def qimage_to_image(img: QtGui.QImage):
    buffer = QtCore.QBuffer()
    buffer.open(QtCore.QBuffer.ReadWrite)
    img.save(buffer, "PNG")
    pil_im = Image.open(io.BytesIO(buffer.data()))
    return pil_im