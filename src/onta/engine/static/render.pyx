
from PIL import Image

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