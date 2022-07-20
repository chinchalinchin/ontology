import os
from PIL import Image
import onta.settings as settings
import onta.load.conf as conf

class Repo():

    tiles = {}
    struts = {}
    sprites = {}

    def __init__(self):
        self._init_tiles()

    def _init_tiles(self):
        tiles_conf = conf.configuration('tiles')
        for tile_key, tile_conf in tiles_conf.items():
            image_conf = tile_conf['image']
            image_path = os.path.join(settings.TILE_DIR, image_conf['file'])
            x, y = image_conf['position']['x'], image_conf['position']['y']
            w, h = image_conf['size']['width'], image_conf['size']['height']
            buffer = Image.open(image_path)
            self.tiles[tile_key] = buffer.crop((x,y,w+x,h+y))

if __name__=="__main__":
    repo = Repo()