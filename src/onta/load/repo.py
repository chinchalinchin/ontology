import os
from typing import Union
from PIL import Image

import onta.settings as settings
import onta.load.conf as conf
import onta.util.logger as logger


log = logger.Logger('ontology.onta.repo', settings.LOG_LEVEL)

OBJECTS = ['tiles', 'struts']

class Repo():

    tiles = {}
    struts = {}
    sprites = {}

    def __init__(self) -> None:
        for obj in OBJECTS:
            self._init_assets(obj)

    def _init_assets(self, obj: str) -> None:
        log.debug(f'Initializing {obj} assets', 'Repo._init_assets')
        objects_conf = conf.configuration(obj)

        for obj_key, obj_conf in objects_conf.items():
            image_conf = obj_conf['image']
            x, y = image_conf['position']['x'], image_conf['position']['y']
            w, h = image_conf['size']['width'], image_conf['size']['height']

            if obj == OBJECTS[0]:
                image_path = os.path.join(settings.TILE_DIR, image_conf['file'])
            elif obj == OBJECTS[1]:
                image_path = os.path.join(settings.STRUT_DIR, image_conf['file'])

            buffer = Image.open(image_path)
            buffer = buffer.convert(settings.IMG_MODE)

            log.debug( f"{obj} configuration: {buffer.format} - {buffer.size}x{buffer.mode}", 
                'Repo._init_assets')

            if obj == OBJECTS[0]:
                self.tiles[obj_key] = buffer.crop((x,y,w+x,h+y))
            elif obj == OBJECTS[1]:
                self.struts[obj_key] = buffer.crop((x,y,w+x,h+y))


    def get_asset(self, obj: str, obj_key: str) -> Union[Image.Image, None]:
        if obj == OBJECTS[0]:
            return self.tiles.get(obj_key)
        if obj == OBJECTS[1]:
            return self.struts.get(obj_key)
        return None


if __name__=="__main__":
    repo = Repo()