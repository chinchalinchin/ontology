import os
from typing import Union
from PIL import Image

import onta.settings as settings
import onta.load.conf as conf

OBJECTS = ['tiles', 'struts']

class Repo():

    tiles = {}
    struts = {}
    sprites = {}

    def __init__(self) -> None:
        for obj in OBJECTS:
            self._init_objects(obj)

    def _init_objects(self, obj: str) -> None:
        objects_conf = conf.configuration(obj)
        for obj_key, obj_conf in objects_conf.items():
            image_conf = obj_conf['image']
            image_path = os.path.join(settings.TILE_DIR, image_conf['file'])
            
            x, y = image_conf['position']['x'], image_conf['position']['y']
            w, h = image_conf['size']['width'], image_conf['size']['height']

            buffer = Image.open(image_path)

            if obj == OBJECTS[0]:
                self.tiles[obj_key] = buffer.crop((x,y,w+x,h+y))
            elif obj == OBJECTS[1]:
                self.structs[obj_key] = buffer.crop((x,y,w+x,h+y))


    def get_object(self, obj: str, obj_key: str) -> Union[Image.Image, None]:
        if obj == OBJECTS[0]:
            return self.tiles.get(obj_key)
        if obj == OBJECTS[1]:
            return self.struts.get(obj_key)
        return None


if __name__=="__main__":
    repo = Repo()