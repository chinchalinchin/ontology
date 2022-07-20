import os
from typing import Union
from PIL import Image

import onta.settings as settings
import onta.load.conf as conf
import onta.util.logger as logger
import onta.util.gui as gui


log = logger.Logger('ontology.onta.repo', settings.LOG_LEVEL)

LAYERS = ['tiles', 'struts']

class Repo():

    tiles = {}
    struts = {}
    sprites = {}

    def __init__(self) -> None:
        for layer in LAYERS:
            self._init_layers(layer)
        self._init_sprites()

    def _init_layers(self, layer: str) -> None:
        log.debug(f'Initializing {layer} assets', 'Repo._init_assets')
        layers_conf = conf.configuration(layer)

        for layer_key, layer_conf in layers_conf.items():
            image_conf = layer_conf['image']
            x, y = image_conf['position']['x'], image_conf['position']['y']
            w, h = image_conf['size']['w'], image_conf['size']['h']

            if layer == LAYERS[0]:
                image_path = os.path.join(settings.TILE_DIR, image_conf['file'])
            elif layer == LAYERS[1]:
                image_path = os.path.join(settings.STRUT_DIR, image_conf['file'])

            buffer = Image.open(image_path)
            buffer = buffer.convert(settings.IMG_MODE)

            log.debug( f"{layer} configuration: {buffer.format} - {buffer.size}x{buffer.mode}", 
                'Repo._init_assets')

            if layer == LAYERS[0]:
                self.tiles[layer_key] = buffer.crop((x,y,w+x,h+y))

            elif layer == LAYERS[1]:
                self.struts[layer_key] = buffer.crop((x,y,w+x,h+y))


    def _init_sprites(self) -> None:
        sprites_conf = conf.configuration('sprites')

        for sprite_conf_key, sprite_conf in sprites_conf.items():
            self.sprites[sprite_conf_key] = {}
            sprite_dim = (sprite_conf['size']['w'], sprite_conf['size']['h'])
            sprite_sheets = sprite_conf['sheets']['compose']
            sprite_states = sprite_conf['states']
            sheets = []

            for sheet in sprite_sheets:
                sheet_path = os.path.join(settings.SPRITE_DIR, sheet['file'])
                sheet_img = Image.open(sheet_path)
                sheet_img = sheet_img.convert(settings.IMG_MODE)
                sheets.append(sheet_img)

            for state_conf in sprite_states:
                state_key = list(state_conf.keys())[0]
                state_row = state_conf[state_key]['row']
                state_frames = state_conf[state_key]['frames']
                self.sprites[sprite_conf_key][state_key] = []

                start_y = state_row * sprite_dim[1]
                for i in range(state_frames):
                    start_x = i*sprite_dim[0]
                    crop_box = (start_x, start_y, 
                        start_x + sprite_dim[0], start_y + sprite_dim[1])
                    
                    crop_sheets = []

                    for sheet in sheets:
                        crop_sheets.append(sheet.crop(crop_box))
                
                    sprite_state_frame = gui.new_image(sprite_dim)

                    i = 0
                    for sheet in crop_sheets:
                        sprite_state_frame.paste(sheet, (0,0), sheet)

                    self.sprites[sprite_conf_key][state_key].append(sprite_state_frame)


    def get_layer(self, layer: str, layer_key: str) -> Union[Image.Image, None]:
        if layer == LAYERS[0]:
            return self.tiles.get(layer_key)
        if layer == LAYERS[1]:
            return self.struts.get(layer_key)
        return None

    def get_sprite(self, sprite: str, state: str, frame: int):
        return self.sprites[sprite][state][frame]

if __name__=="__main__":
    repository = Repo()
    frame = repository.get_sprite('hero', 'walk_down', 1)
    frame.show()