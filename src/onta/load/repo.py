import os
from typing import Union
from PIL import Image

import onta.settings as settings
import onta.load.conf as conf
import onta.util.logger as logger
import onta.util.gui as gui


log = logger.Logger('onta.repo', settings.LOG_LEVEL)

STATIC_ASSETS_TYPES = ['tiles', 'struts', 'plates']
SWITCH_PLATES_TYPES = ['container', 'pressure', 'gate']

class Repo():

    tiles = {}
    struts = {}
    plates = {}
    tracks = {}
    sprites = {}
    effects = {}
    displays = {}
    avatars = {}
    mirrors = {}
    slots = {}

    def __init__(self, ontology_path: str) -> None:
        """
        .. note:
            - No reference is kept to `ontology_path`; it is passed to initialize methods and released.
        """
        config = conf.Conf(ontology_path)
        for asset_type in STATIC_ASSETS_TYPES:
            self._init_static_assets(asset_type, config, ontology_path)
        self._init_sprite_assets(config, ontology_path)
        self._init_interface_assets(config, ontology_path)

    def _init_static_assets(self, asset_type: str, config: conf.Conf, ontology_path: str) -> None:
        log.debug(f'Initializing {asset_type} assets...', 'Repo._init_static_assets')

        if asset_type == 'tiles':
            assets_conf = config.load_tile_configuration()
        elif asset_type == 'struts':
            asset_props, assets_conf = config.load_strut_configuration()
        elif asset_type == 'plates':
            asset_props, assets_conf = config.load_plate_configuration()

        for asset_key, asset_conf in assets_conf.items():
            w, h = asset_conf['size']['w'], asset_conf['size']['h']

            if asset_conf.get('file') is not None:
                if asset_type == 'plates' and asset_props[asset_key].get('type') in SWITCH_PLATES_TYPES:
                    on_x, on_y = asset_conf['file']['on_position']['x'], asset_conf['file']['on_position']['y']
                    off_x, off_y = asset_conf['file']['off_position']['x'], asset_conf['file']['off_position']['y']
                else:
                    x, y = asset_conf['file']['position']['x'], asset_conf['file']['position']['y']

                if asset_type == 'tiles':
                    image_path = os.path.join(
                        ontology_path, 
                        *settings.TILE_PATH, 
                        asset_conf['file']['path']
                    )
                elif asset_type == 'struts':
                    image_path = os.path.join(
                        ontology_path, 
                        *settings.STRUT_PATH, 
                        asset_conf['file']['path']
                    )
                elif asset_type == 'plates':                         
                    image_path = os.path.join(
                        ontology_path, 
                        *settings.PLATE_PATH, 
                        asset_conf['file']['path']
                    )

                buffer = Image.open(image_path).convert(settings.IMG_MODE)

                log.debug( f"{asset_key} configuration: size - {buffer.size}, mode - {buffer.mode}", 
                    'Repo._init_static_assets')

                if asset_type == 'tiles':
                    self.tiles[asset_key] = buffer.crop((x,y,w+x,h+y))
                elif asset_type == 'struts':
                    self.struts[asset_key] = buffer.crop((x,y,w+x,h+y))
                elif asset_type == 'plates':
                    if asset_props[asset_key].get('type') in SWITCH_PLATES_TYPES:
                        self.plates[asset_key] = {}
                        self.plates[asset_key]['on'] = buffer.crop((on_x,on_y,w+on_x,h+on_y))
                        self.plates[asset_key]['off'] = buffer.crop((off_x,off_y,w+off_x,h+off_y))
                    else:
                        self.plates[asset_key] = buffer.crop((x,y,w+x,h+y))
                    
            elif asset_conf.get('channels') is not None:
                # TODO: on/off switch plate channels, currently using channels on switch plates will break this method

                channels = (
                    asset_conf['channels']['r'], 
                    asset_conf['channels']['g'],
                    asset_conf['channels']['b'],
                    asset_conf['channels']['a']
                )
                buffer = Image.new(settings.IMG_MODE, (w,h), channels)
                if asset_type == 'tiles':
                    self.tiles[asset_key] = buffer
                elif asset_type == 'struts':
                    self.struts[asset_key] = buffer
                elif asset_type == 'plates':
                    self.plates[asset_key] = buffer
 

    def _init_interface_assets(self, config: conf.Conf, ontology_path: str) -> None:
        log.debug(f'Initializing  assets...', 'Repo._init_interface_assets')
        interface_conf = config.load_interface_configuration()
        for size in interface_conf['sizes']:
            for interset_key, interset in interface_conf['hud'][size].items():
                if interset_key == 'display':
                    x, y = interset['image']['file']['x'], interset['image']['file']['y']
                    w, h = interset['image']['size']['w'], interset['image']['size']['h']
                    image_path = os.path.join(
                        ontology_path,
                        *settings.DISPLAY_PATH,
                        interset['image']['file']['path']
                    )
                    buffer = Image.open(image_path).convert(settings.IMG_MODE)
                    log.debug( f"{interset_key} configuration: size - {buffer.size}, mode - {buffer.mode}", 
                        'Repo._init_interface_assets')
                    self.displays[size] = buffer.crop((x,y,w+x,h+y))
                    
                # TODO
                
                # elif interset_key == 'slots':
                #     image_path = os.path.join(
                #         ontology_path,
                #         *settings.SLOT_PATH,
                #         interset['image']['file']['path']
                #     )
                # elif interset_key == 'mirrors':
                #     image_path = os.path.join(
                #         ontology_path,
                #         *settings.MIRROR_PATH,
                #         interset['image']['file']['path']
                #     )
                # elif interset_key == 'avatars':
                #     image_path = os.path.join(
                #         ontology_path,
                #         *settings.AVATAR_PATH,
                #         interset['image']['file']['path']
                #   )

                # buffer = Image.open(image_path).convert(settings.IMG_MODE)
                # log.debug( f"{interset_key} configuration: size - {buffer.size}, mode - {buffer.mode}", 
                #     'Repo._init_interface_assets')
                
                # if interset_key == 'display':
                #     self.displays[size] = buffer.crop((x,y,w+x,h+y))

                # elif component_key == 'slots':
                #     self.slots[size] = buffer.crop((x,y,w+x,h+y))
                # elif component_key == 'mirrors':
                #     self.mirrors[size] = buffer.crop((x,y,w+x,h+y))
                # elif component_key == 'avatars':
                #     self.mirrors[size] = buffer.crop((x,y,w+x,h+y))

    def _init_sprite_assets(self, config: conf.Conf, ontology_path: str) -> None:
        log.debug('Initializing sprite assets...', 'Repo._init_sprite_assets')

        states_conf, props_conf, sheets_conf = config.load_sprite_configuration()

        for sprite_key, sheet_conf in sheets_conf.items():
            sprite_dim = props_conf[sprite_key]['size']['w'], props_conf[sprite_key]['size']['h']
            
            sheets, self.sprites[sprite_key] = [], {}

            for sheet in sheet_conf:
                sheet_path = os.path.join(ontology_path, *settings.SPRITE_PATH, sheet)
                sheet_img = Image.open(sheet_path).convert(settings.IMG_MODE)
                sheets.append(sheet_img)
                
            frames = 0
            for state_key, state_conf in states_conf[sprite_key].items():
                state_row, state_frames = state_conf['row'], state_conf['frames']
                frames += state_frames
                self.sprites[sprite_key][state_key] = []

                start_y = state_row * sprite_dim[1]
                for i in range(state_frames):
                    start_x = i*sprite_dim[0]
                    crop_box = (start_x, start_y, 
                        start_x + sprite_dim[0], start_y + sprite_dim[1])
                    
                    crop_sheets = []

                    for sheet in sheets:
                        crop_sheets.append(sheet.crop(crop_box))
                
                    sprite_state_frame = gui.new_image(sprite_dim)

                    for sheet in crop_sheets:
                        sprite_state_frame.paste(sheet, (0,0), sheet)

                    self.sprites[sprite_key][state_key].append(sprite_state_frame)

            log.debug(f'{sprite_key} configuration: states - {len(self.sprites[sprite_key])}, frames - {frames}', 'Repo._init_sprites')


    def get_asset_frame(self, asset_key: str, element_key: str) -> Union[Image.Image, None]:
        if asset_key == 'tiles':
            return self.tiles.get(element_key)
        if asset_key == 'struts':
            return self.struts.get(element_key)
        if asset_key == 'plates':
            return self.plates.get(element_key)
        return None


    def get_sprite_frame(self, sprite: str, state: str, frame: int):
        return self.sprites[sprite][state][frame]

if __name__=="__main__":
    repository = Repo()
    frame = repository.get_sprite('hero', 'walk_down', 1)
    frame.show()