import os
from typing import Union
from PIL import Image

import onta.settings as settings
import onta.load.conf as conf
import onta.util.logger as logger
import onta.util.gui as gui


log = logger.Logger('onta.repo', settings.LOG_LEVEL)

ASSETS = ['tiles', 'struts', 'plates']

class Repo():

    tiles = {}
    struts = {}
    plates = {}
    sprites = {}

    def __init__(self, config: conf.Conf) -> None:
        """
        .. note:
            - No reference is kept to `config`; it is passed to initialize methods and released unaltered.
        """
        for asset in ASSETS:
            self._init_assets(asset, config)
        self._init_sprites(config)

    def _init_assets(self, asset: str, config: conf.Conf) -> None:
        log.debug(f'Initializing {asset} asset', 'Repo._init_assets')
        layers_conf = config.configuration(asset)

        for layer_key, layer_conf in layers_conf.items():
            image_conf = layer_conf['image']
            w, h = image_conf['size']['w'], image_conf['size']['h']

            if image_conf.get('file') is not None:
                x, y = image_conf['position']['x'], image_conf['position']['y']
                w, h = image_conf['size']['w'], image_conf['size']['h']

                if asset == 'tiles':
                    image_path = os.path.join(settings.TILE_DIR, image_conf['file'])
                elif asset == 'struts':
                    image_path = os.path.join(settings.STRUT_DIR, image_conf['file'])
                elif asset == 'plates': 
                    image_path = os.path.join(settings.PLATE_DIR, image_conf['file'])

                buffer = Image.open(image_path).convert(settings.IMG_MODE)

                log.debug( f"{layer_key} configuration: {buffer.format} - {buffer.size}x{buffer.mode}", 
                    'Repo._init_assets')

                if asset == 'tiles':
                    self.tiles[layer_key] = buffer.crop((x,y,w+x,h+y))
                elif asset == 'struts':
                    self.struts[layer_key] = buffer.crop((x,y,w+x,h+y))
                elif asset == 'plates':
                    self.plates[layer_key] = buffer.crop((x,y,w+x,h+y))
                    
            elif image_conf.get('channels') is not None:
                channels = (
                    image_conf['channels']['r'], 
                    image_conf['channels']['g'],
                    image_conf['channels']['b'],
                    image_conf['channels']['a']
                )
                buffer = Image.new(settings.IMG_MODE, (w,h), channels)
                if asset == 'tiles':
                    self.tiles[layer_key] = buffer
                elif asset == 'struts':
                    self.struts[layer_key] = buffer
                elif asset == 'plates':
                    self.plates[layer_key] = buffer
 

    def _init_sprites(self, config) -> None:
        sprites_conf = config.configuration('sprites')

        for sprite_conf_key, sprite_conf in sprites_conf.items():
            self.sprites[sprite_conf_key] = {}
            sprite_dim = (sprite_conf['size']['w'], sprite_conf['size']['h'])
            sprite_sheets = sprite_conf['sheets']['compose']
            sprite_states = sprite_conf['states']
            sheets = []

            for sheet in sprite_sheets:
                sheet_path = os.path.join(settings.SPRITE_DIR, sheet['file'])
                sheet_img = Image.open(sheet_path).convert(settings.IMG_MODE)
                sheets.append(sheet_img)

            for state_conf in sprite_states:
                state_key = list(state_conf.keys())[0]
                state_row = state_conf[state_key]['row']
                state_frames = state_conf[state_key]['frames']

                # here is where the repo is aware of the frames per state
                # how to get this to the world?
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


    def get_asset(self, layer: str, layer_key: str) -> Union[Image.Image, None]:
        if layer == 'tiles':
            return self.tiles.get(layer_key)
        if layer == 'struts':
            return self.struts.get(layer_key)
        if layer == 'plates':
            return self.plates.get(layer_key)
        return None

    def get_sprite(self, sprite: str, state: str, frame: int):
        return self.sprites[sprite][state][frame]

    def get_sprite_state_frames(self, sprite: str, state: str):
        return len(self.sprites[sprite][state])

    def enumerate_sprite_state_frames(self):
        enum_state_frames = {}
        for sprite_key, sprite_conf in self.sprites.items():
            enum_state_frames[sprite_key] = {}
            for state_key, state_conf in sprite_conf.items():
                enum_state_frames[sprite_key][state_key] = len(state_conf)
        return enum_state_frames

if __name__=="__main__":
    repository = Repo()
    frame = repository.get_sprite('hero', 'walk_down', 1)
    frame.show()