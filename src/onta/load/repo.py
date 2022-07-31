import os
from typing import Union
from PIL import Image

import onta.settings as settings
import onta.load.conf as conf
import onta.util.logger as logger
import onta.util.gui as gui


log = logger.Logger('onta.repo', settings.LOG_LEVEL)

STATIC_ASSETS_TYPES = [ 'tiles', 'struts', 'plates' ]
SWITCH_PLATES_TYPES = [ 'container', 'pressure', 'gate' ]
UNITLESS_UI_TYPES = [ 'slots', 'avatars' ]

class Repo():

    tiles = {}
    struts = {}
    plates = {}
    tracks = {}
    sprites = {}
    effects = {}
    avatars = {}
    mirrors = {}
    slots = {}
    equipment = {}


    @staticmethod
    def adjust_cap_rotation(direction):
        # I am convinced there is an easier way to calculate this using arcosine and arcsine,
        # but i don't feel like thinking about domains and ranges right now...
        if direction == 'left':
            left_adjust, right_adjust = 0, 180
            up_adjust, down_adjust = 90, 270
        elif direction == 'right':
            left_adjust, right_adjust = 180, 0
            up_adjust, down_adjust = 270, 90
        elif direction == 'up':
            left_adjust, right_adjust = 90, 270
            up_adjust, down_adjust = 0, 180
        else:
            left_adjust, right_adjust = 270, 90
            up_adjust, down_adjust = 180, 0
        return (up_adjust, left_adjust, right_adjust, down_adjust)


    @staticmethod
    def adjust_buffer_rotation(direction):
        if direction == 'vertical':
            return (0, 90)
        return (90, 0)


    def __init__(self, ontology_path: str) -> None:
        """
        .. note::
            No reference is kept to `ontology_path`; it is passed to initialize methods and released.
        """
        config = conf.Conf(ontology_path)
        self._init_static_assets(config, ontology_path)
        self._init_sprite_assets(config, ontology_path)
        self._init_unitless_hud_assets(config, ontology_path)
        self._init_metered_hud_assets(config, ontology_path)
        self._init_menu_assets(config, ontology_path)


    def _init_static_assets(self, config: conf.Conf, ontology_path: str) -> None:

        for asset_type in STATIC_ASSETS_TYPES:
            log.debug(f'Initializing {asset_type} assets...', 'Repo._init_static_assets')

            if asset_type == 'tiles':
                assets_conf = config.load_tile_configuration()
                w, h = assets_conf['tile']['w'], assets_conf['tile']['h']
            elif asset_type == 'struts':
                asset_props, assets_conf = config.load_strut_configuration()
            elif asset_type == 'plates':
                asset_props, assets_conf = config.load_plate_configuration()

            for asset_key, asset_conf in assets_conf.items():
                # need tile dimensions here...but tile dimensions don't exist until world
                # pulls static state...
                if asset_type != 'tiles':
                    w, h = asset_conf['size']['w'], asset_conf['size']['h']

                if asset_conf.get('path'):
                    if asset_type == 'plates' and asset_props[asset_key].get('type') in SWITCH_PLATES_TYPES:
                        on_x, on_y = asset_conf['position']['on_position']['x'], asset_conf['position']['on_position']['y']
                        off_x, off_y = asset_conf['position']['off_position']['x'], asset_conf['position']['off_position']['y']
                    else:
                        x, y = asset_conf['position']['x'], asset_conf['position']['y']

                    if asset_type == 'tiles':
                        image_path = os.path.join(
                            ontology_path, 
                            *settings.TILE_PATH, 
                            asset_conf['path']
                        )
                    elif asset_type == 'struts':
                        image_path = os.path.join(
                            ontology_path, 
                            *settings.STRUT_PATH, 
                            asset_conf['path']
                        )
                    elif asset_type == 'plates':                         
                        image_path = os.path.join(
                            ontology_path, 
                            *settings.PLATE_PATH, 
                            asset_conf['path']
                        )

                    buffer = Image.open(image_path).convert(settings.IMG_MODE)

                    # TODO: check if channels exist and then modify as appropriate

                    log.debug( f"{asset_key} configuration: size - {buffer.size}, mode - {buffer.mode}", 
                        'Repo._init_static_assets')

                    if asset_type == 'tiles':
                        self.tiles[asset_key] = buffer.crop((x,y,w+x,h+y))
                    elif asset_type == 'struts':
                        self.struts[asset_key] = buffer.crop((x,y,w+x,h+y))
                    elif asset_type == 'plates':
                        if asset_props[asset_key].get('type') in SWITCH_PLATES_TYPES:
                            self.plates[asset_key] = {
                                'on': buffer.crop((on_x,on_y,w+on_x,h+on_y)),
                                'off': buffer.crop((off_x,off_y,w+off_x,h+off_y))
                            }
                        else:
                            self.plates[asset_key] = buffer.crop((x,y,w+x,h+y))
                        
                elif asset_conf.get('channels'):
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
                        if asset_props[asset_key].get('type') in SWITCH_PLATES_TYPES:
                            self.plates[asset_key] = {
                                'on': buffer,
                                'off': buffer
                            }
                        else:
                            self.plates[asset_key] = buffer
 

    def _init_unitless_hud_assets(self, config: conf.Conf, ontology_path: str) -> None:
        interface_conf = config.load_interface_configuration()
        for size in interface_conf['sizes']:
            self.slots[size], self.avatars[size] = {}, {}
            self.slots[size]['slot'] = {}

            for interfaceset_key in UNITLESS_UI_TYPES:
                interfaceset = interface_conf['hud'][size][interfaceset_key]
                log.debug(f'Initializing {interfaceset_key} assets...', 'Repo._init_interface_assets')
                
                for interface_key, interface in interfaceset.items():
                    if interface:
                        w, h = interface['size']['w'], interface['size']['h']   

                        if interface.get('path'):
                            x, y = interface['position']['x'], interface['position']['y']
                            
                            if interfaceset_key == 'slots':
                                sub_path = settings.SLOT_PATH
                            elif interfaceset_key == 'avatars':
                                sub_path = settings.AVATAR_PATH
         
                            image_path = os.path.join(
                                    ontology_path,
                                    *sub_path,
                                    interface['path']
                                )
                            buffer = Image.open(image_path).convert(settings.IMG_MODE)

                            # TODO: check if channels exist and then apply as appropriate

                        elif interface.get('channels'):
                            channels = (
                                interface['channels']['r'], 
                                interface['channels']['g'],
                                interface['channels']['b'],
                                interface['channels']['a']
                            )
                            buffer = Image.new(settings.IMG_MODE, (w,h), channels)
                        
                        if buffer:
                            log.debug( f"{interfaceset_key} {interface_key} configuration: size - {buffer.size}, mode - {buffer.mode}", 
                                'Repo._init_interface_assets')

                            slot_props = interface_conf['hud'][size]['slots']
                            buffer = buffer.crop((x,y,w+x,h+y))
                            if interface_key == 'cap':
                                (down_adjust, left_adjust, right_adjust, up_adjust) = \
                                    self.adjust_cap_rotation(
                                        slot_props['cap']['definition']
                                    )
                                self.slots[size][interface_key] = {
                                    'up': buffer.rotate(
                                        up_adjust,
                                        expand=True
                                    ),
                                    'left': buffer.rotate(
                                        left_adjust,
                                        expand=True
                                    ),
                                    'right': buffer.rotate(
                                        right_adjust,
                                        expand=True
                                    ),
                                    'down': buffer.rotate(
                                        down_adjust,
                                        expand=True
                                    )
                                }
                            elif interface_key == 'buffer':
                                (vertical_adjust, horizontal_adjust) = \
                                    self.adjust_buffer_rotation(
                                    slot_props['buffer']['definition']  
                                )
                                self.slots[size][interface_key] = {
                                    'vertical': buffer.rotate(
                                        vertical_adjust,
                                        expand=True
                                    ),
                                    'horizontal': buffer.rotate(
                                        horizontal_adjust,
                                        expand=True
                                    )
                                }
                            elif interface_key in ['empty', 'equipped']:
                                self.slots[size]['slot'][interface_key] = buffer


    def _init_metered_hud_assets(self, config: conf.Conf, ontology_path: str) -> None:
        interface_conf = config.load_interface_configuration()

        for size in interface_conf['sizes']:
            self.mirrors[size] = {}
            mirror_set = interface_conf['hud'][size]['mirrors']

            for mirror_key, mirror in mirror_set.items():
                if mirror:
                    self.mirrors[size][mirror_key] = {}
                    
                    for mirror_fill in ['unit', 'empty']:
                        if mirror[mirror_fill].get('path'):
                            x,y = mirror[mirror_fill]['position']['x'], mirror[mirror_fill]['position']['y']
                            w, h = mirror[mirror_fill]['size']['w'], mirror[mirror_fill]['size']['h']
                            image_path = os.path.join(
                                ontology_path,
                                *settings.MIRROR_PATH,
                                mirror[mirror_fill]['path']
                            )
                            buffer = Image.open(image_path).convert(settings.IMG_MODE)

                            self.mirrors[size][mirror_key][mirror_fill] = buffer.crop((x,y,w+x,h+y))


    def _init_menu_assets(self, config: conf.Conf, ontology_path: str) -> None:
        pass

    def _init_sprite_assets(self, config: conf.Conf, ontology_path: str) -> None:
        log.debug('Initializing sprite assets...', 'Repo._init_sprite_assets')

        states_conf, _, sheets_conf = config.load_sprite_configuration()

        for sprite_key, sheet_conf in sheets_conf.items():
            sprite_dim = (
                sheets_conf[sprite_key]['size']['w'], 
                sheets_conf[sprite_key]['size']['h']
            )
            
            sheets, self.sprites[sprite_key] = [], {}

            for sheet in sheet_conf['sheets']:
                sheet_path = os.path.join(
                    ontology_path, 
                    *settings.SPRITE_PATH, 
                    sheet
                )
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


    def get_form_frame(self, form_key: str, group_key: str) -> Union[Image.Image, None]:
        if form_key in [ 'tiles', 'tile' ]:
            return self.tiles.get(group_key)
        if form_key in [ 'struts', 'strut' ]:
            return self.struts.get(group_key)
        if form_key in [ 'plates', 'plate' ]:
            return self.plates.get(group_key)
        return None


    def get_avatar_frame(self, breakpoint_key, component_key) -> Union[Image.Image, None]:
        if self.avatars.get(breakpoint_key):
            return self.avatars[breakpoint_key].get(component_key)
        return None
    
    def get_slot_frames(self, breakpoint_key, component_key) -> Union[Image.Image, None]:
        if self.slots.get(breakpoint_key):
            return self.slots[breakpoint_key].get(component_key)
        return None
        

    def get_mirror_frame(self, breakpoint_key, component_key, fill_key):
        if self.mirrors.get(breakpoint_key) and self.mirrors[breakpoint_key].get(component_key):
            return self.mirrors[breakpoint_key][component_key].get(fill_key)
        return None

    def get_sprite_frame(self, sprite: str, state: str, frame: int) -> Union[Image.Image, None]:
        return self.sprites[sprite][state][frame]
