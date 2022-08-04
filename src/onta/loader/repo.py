import os
from typing import Union
from PIL import Image
import munch

import onta.settings as settings
import onta.loader.conf as conf
import onta.util.logger as logger
import onta.util.gui as gui


log = logger.Logger('onta.repo', settings.LOG_LEVEL)

STATIC_ASSETS_TYPES = [ 'tiles', 'struts', 'plates' ]
SWITCH_PLATES_TYPES = [ 'container', 'pressure', 'gate' ]
AVATAR_TYPES = [ 'armor', 'equipment', 'inventory', 'quantity' ]
APPAREL_TYPES = [ 'armor', 'equipment' ]

class Repo():

    tiles = munch.Munch({})
    struts = munch.Munch({})
    plates = munch.Munch({})
    tracks = munch.Munch({})
    pixies = munch.Munch({})
    nymphs = munch.Munch({})
    sprites = munch.Munch({})

    # todo: base and accent attr
    sprite_bases = {}
    sprite_accents = {}
    
    avatars = munch.Munch({})
    bottles = munch.Munch({})
    mirrors = munch.Munch({})
    menus = munch.Munch({})
    slots = munch.Munch({})
    packs = munch.Munch({})
    apparel = munch.Munch({})


    @staticmethod
    def adjust_cap_rotation(
        direction: str
    ) -> tuple:
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
    def adjust_buffer_rotation(
        direction: str
    ) -> tuple:
        if direction == 'vertical':
            return (0, 90)
        return (90, 0)


    @staticmethod
    def open_image():
        pass


    def __init__(
        self, 
        ontology_path: str
    ) -> None:
        """
        .. note::
            No reference is kept to `ontology_path`; it is passed to initialize methods and released.
        """
        config = conf.Conf(ontology_path)
        self._init_form_assets(
            config, 
            ontology_path
        )
        self._init_entity_assets(
            config, 
            ontology_path
        )
        self._init_apparel_assets(
            config,
            ontology_path
        )
        self._init_sense_assets(
            config, 
            ontology_path
        )
        self._init_avatar_assets(
            config,
            ontology_path
        )


    def _init_form_assets(
        self, config: 
        conf.Conf, 
        ontology_path: str
    ) -> None:
        """_summary_

        :param config: _description_
        :type config: conf.Conf
        :param ontology_path: _description_
        :type ontology_path: str

        .. note::
            - Static assets, i.e. _Tile_\s, _Strut_\s & _Plate_\s can be rendered using RGBA channels instead of a cropping a sheet file into an PIL image. If the channels are specified through the configuration file for the appropriate _Form_ asset, the asset frame will be created using through channels. Particularly useful if you need to create an inside door with a transculent light square leading back outside.
        """

        for asset_type in STATIC_ASSETS_TYPES:
            log.debug(
                f'Initializing {asset_type} assets...', 
                'Repo._init_static_assets'
            )

            if asset_type == 'tiles':
                assets_conf = config.load_tile_configuration()
                w, h = (
                    assets_conf.tile.w, 
                    assets_conf.tile.h
                )
            elif asset_type == 'struts':
                asset_props, assets_conf = config.load_strut_configuration()
            elif asset_type == 'plates':
                asset_props, assets_conf = config.load_plate_configuration()

            for asset_key, asset_conf in assets_conf.items():
                # need tile dimensions here...but tile dimensions don't exist until world
                # pulls static state...
                if asset_type != 'tiles':
                    w, h = (
                        asset_conf.size.w, 
                        asset_conf.size.h
                    )

                if asset_conf.get('path'):
                    if asset_type == 'plates' and \
                        asset_props.get(asset_key).get('type') in SWITCH_PLATES_TYPES:
                        on_x, on_y = (
                            asset_conf.position.on_position.x, 
                            asset_conf.position.on_position.y
                        )
                        off_x, off_y = (
                            asset_conf.position.off_position.x, 
                            asset_conf.position.off_position.y
                        )
                    else:
                        x, y = (
                            asset_conf.position.x, 
                            asset_conf.position.y
                        )

                    if asset_type == 'tiles':
                        image_path = os.path.join(
                            ontology_path, 
                            *settings.TILE_PATH, 
                            asset_conf.path
                        )
                    elif asset_type == 'struts':
                        image_path = os.path.join(
                            ontology_path, 
                            *settings.STRUT_PATH, 
                            asset_conf.path
                        )
                    elif asset_type == 'plates':                         
                        image_path = os.path.join(
                            ontology_path, 
                            *settings.PLATE_PATH, 
                            asset_conf.path
                        )

                    buffer = gui.open_image(
                        image_path
                    )

                    log.debug(
                        f"{asset_key} configuration: size - {buffer.size}, mode - {buffer.mode}", 
                        'Repo._init_static_assets'
                    )

                    if asset_type == 'tiles':
                        setattr(
                            self.tiles,
                            asset_key,
                            buffer.crop(
                                (
                                    x,
                                    y,
                                    w + x,
                                    h + y
                                )
                            )
                        )
                    elif asset_type == 'struts':
                        setattr(
                            self.struts,
                            asset_key,
                            buffer.crop(
                                (
                                    x,
                                    y,
                                    w + x,
                                    h + y
                                )
                            )
                        )
                    elif asset_type == 'plates':
                        if asset_props[asset_key].get('type') in SWITCH_PLATES_TYPES:
                            setattr(
                                self.plates,
                                asset_key,
                                munch.Munch({
                                    'on': buffer.crop(
                                        (
                                            on_x,
                                            on_y,
                                            w + on_x,
                                            h + on_y)
                                    ),
                                    'off': buffer.crop(
                                        (
                                            off_x,
                                            off_y,
                                            w + off_x,
                                            h + off_y
                                        )
                                    )
                                })
                            )
                        else:
                            setattr(
                                self.plates,
                                asset_key,
                                buffer.crop(
                                    (
                                        x,
                                        y,
                                        w + x,
                                        h + y
                                    )
                                )
                            )
                        
                elif asset_conf.get('channels'):
                    channels = (
                        asset_conf.channels.r, 
                        asset_conf.channels.g,
                        asset_conf.channels.b,
                        asset_conf.channels.a
                    )
                    buffer = gui.channels(
                        (
                            w,
                            h
                        ),
                        channels
                    )

                    if asset_type == 'tiles':
                        setattr(
                            self.tiles,
                            asset_key,
                            buffer
                        )
                    elif asset_type == 'struts':
                        setattr(
                            self.struts,
                            asset_key,
                            buffer
                        )
                    elif asset_type == 'plates':
                        if asset_props[asset_key].get('type') in SWITCH_PLATES_TYPES:
                            setattr(
                                self.plates,
                                asset_key,
                                munch.Munch({
                                    'on': buffer,
                                    'off': buffer
                                })
                            )
                        else:
                            setattr(
                                self.plates,
                                asset_key,
                                buffer
                            )
 

    def _init_sense_assets(
        self, 
        config: conf.Conf, 
        ontology_path: str
    ) -> None:
        """_summary_

        :param config: _description_
        :type config: conf.Conf
        :param ontology_path: _description_
        :type ontology_path: str

        .. note::
            A _Slot_ is defined in a single direction, but used in multiple directions. When styles are applied the engine will need to be aware which direction the definition is in, so it can rotate the _Slot_ component to its appropriate position based on the declared style. In other words, _Slot_\s are a pain.
        """
        log.debug(
            f'Initializing sense assets...', 
            'Repo._init_sense_assets'
        )

        interface_conf = config.load_sense_configuration()

        for size in interface_conf.sizes:

            if not self.slots.get(size):
                setattr(
                    self.slots,
                    size,
                    munch.Munch({})
                )
            if not self.mirrors.get(size):
                setattr(
                    self.mirrors,
                    size,
                    munch.Munch({})
                )
            if not self.packs.get(size):
                setattr(
                    self.packs,
                    size,
                    munch.Munch({})
                )
            if not self.menus.get(size):
                setattr(
                    self.menus,
                    size,
                    munch.Munch({})
                )

            slotset = interface_conf.hud.get(size).slots
            
            ## SLOT INITIALIZATION
            #   NOTE: for (disabled, {slot}), (enabled, {slot}), (active, {slot}), 
            #               (cap, {slot}), (buffer, {slot})
            for slot_key, slot in slotset.items():
                if not slot or not slot.get('path'):
                    continue

                w, h = (
                    slot.size.w, 
                    slot.size.h
                )   
                x, y = (
                    slot.position.x, 
                    slot.position.y
                )

                buffer = gui.open_image(
                    os.path.join(
                        ontology_path,
                        *settings.SENSES_PATH,
                        slot.path
                    )
                )

                log.debug( 
                    f"Slot {slot_key} configuration: size - {buffer.size}, mode - {buffer.mode}", 
                    'Repo._init_interface_assets'
                )

                slot_conf = interface_conf.hud.get(size).slots
                buffer = buffer.crop(
                    (
                        x,
                        y,
                        w + x,
                        h + y
                    )
                )

                # this is annoying, but necessary to allow slots to be rotated...
                if slot_key == 'cap':
                    adjust = \
                        self.adjust_cap_rotation(
                            slot_conf.cap.definition
                        )
                    setattr(
                        self.slots.get(size),
                        slot_key,
                        munch.Munch({
                            'down': buffer.rotate(
                                adjust[0],
                                expand=True
                            ),
                            'left': buffer.rotate(
                                adjust[1],
                                expand=True
                            ),
                            'right': buffer.rotate(
                                adjust[2],
                                expand=True
                            ),
                            'up': buffer.rotate(
                                adjust[3],
                                expand=True
                            ),
                        })
                    )
                elif slot_key == 'buffer':
                    adjust = \
                        self.adjust_buffer_rotation(
                            slot_conf.buffer.definition 
                        )
                    setattr(
                        self.slots.get(size),
                        slot_key,
                        munch.Munch({
                            'vertical': buffer.rotate(
                            adjust[0],
                            expand=True
                            ),
                            'horizontal': buffer.rotate(
                                adjust[1],
                                expand=True
                            )
                        })
                    )
                elif slot_key in [
                    'disabled', 
                    'enabled', 
                    'active'
                ]:
                    setattr(
                        self.slots.get(size),
                        slot_key,
                        buffer
                    )

            ########################
            # TODO: everything ever slot can be parameterized in a loop to condense this method
            #       However, should it be parameterized?

            mirror_set = interface_conf.hud.get(size).mirrors

            ## MIRROR INITIALIZATION
            # NOTE: For (life, {mirror}), (magic, {mirror})
            for mirror_key, mirror in mirror_set.items():
                if not mirror:
                    continue

                if not self.mirrors.get(size).get(mirror_key):
                    setattr(
                        self.mirrors.get(size),
                        mirror_key,
                        munch.Munch({})
                    )
                
                # for (unit, fill), (empty, fill)
                for fill_key, fill in mirror.items():
                    if not fill.get('path'):
                        continue

                    x,y = (
                        fill.position.x, 
                        fill.position.y
                    )
                    w, h = (
                        fill.size.w, 
                        fill.size.h
                    )
                    
                    buffer = gui.open_image(
                        os.path.join(
                            ontology_path,
                            *settings.SENSES_PATH,
                            fill.path
                        )
                    )

                    setattr(
                        self.mirrors.get(size).get(mirror_key),
                        fill_key,
                        buffer.crop(
                            (
                                x,
                                y,
                                w + x,
                                h + y
                            )
                        )
                    )
            ########################

            pack_set = interface_conf.hud.get(size).packs

            ## PACK INITIALIZATION
            # (bag, pack), (belt, pack), (wallet, pack)
            for pack_key, pack in pack_set.items():
                if not pack:
                    continue

                if not self.packs.get(size).get(pack_key):
                    setattr(
                        self.packs.get(size),
                        pack_key,
                        munch.Munch({})
                    )

                for piece_key, piece in pack.items():
                    if not piece.get('path'):
                        continue

                    x, y = (
                        piece.position.x, 
                        piece.position.y
                    )
                    w, h = (
                        piece.size.w, 
                        piece.size.h
                    )

                    buffer = gui.open_image(
                        os.path.join(
                            ontology_path,
                            *settings.SENSES_PATH,
                            piece.path
                        )
                    )

                    setattr(
                        self.packs.get(size).get(pack_key),
                        piece_key,
                        buffer.crop(
                            (
                                x,
                                y,
                                w + x,
                                h + y
                            )
                        )
                    )
            ########################

            button_set = interface_conf.menu.get(size).button

            ## BUTTON INITIALIZATION
            # for (enabled, button), (active, button), (disabled, button)
            for button_key, button in button_set.items():
                if not button:
                    continue

                if not self.menus.get(size).get(button_key):
                    setattr(
                        self.menus.get(size),
                        button_key,
                        munch.Munch({})
                    )
                
                # for (left, piece), (right, piece), (middle, piece)
                for piece_key, piece in button.items():
                    if not piece.get('path'):
                        continue
                    x,y = (
                        piece.position.x, 
                        piece.position.y
                    )
                    w,h = (
                        piece.size.w, 
                        piece.size.h
                    )
                    buffer = gui.open_image(
                        os.path.join(
                            ontology_path,
                            *settings.SENSES_PATH,
                            piece.path
                        )
                    )
                    setattr(
                        self.menus.get(size).get(button_key),
                        piece_key,
                        buffer.crop(
                            (
                                x,
                                y,
                                w + x,
                                h + y
                            )
                        )
                    )
            ##########################


    def _init_avatar_assets(
        self, 
        config: conf.Conf, 
        ontology_path: str
    ) -> None:
        avatar_conf = config.load_avatar_configuration()

        for avatarset_key in AVATAR_TYPES:
            self.avatars[avatarset_key] = {}

            for avatar_key, avatar in avatar_conf['avatars'][avatarset_key].items():
                if not avatar or avatar.get('path') is None:
                    continue

                x,y = (
                    avatar['position']['x'],
                    avatar['position']['y']
                )
                w,h = (
                    avatar['size']['w'],
                    avatar['size']['h']
                )
                image_path = os.path.join(
                    ontology_path,
                    *settings.AVATAR_PATH,
                    avatar['path']
                )
                buffer = Image.open(image_path).convert(settings.IMG_MODE)
                self.avatars[avatarset_key][avatar_key] = buffer.crop(
                    (x,y,w+x,h+y)
                )

        # Bottle Configuration is slightly different, so I wonder if I should separate them
        # conceptually...
        # TODO: !!!
        bottle_conf = avatar_conf['avatars']['bottles']


    def _init_apparel_assets(
        self,
        config: conf.Conf,
        ontology_path: str
    ) -> None:
        apparel_conf = config.load_apparel_configuration()
        # NOTE: skip properties and sheet configuration
        states_conf, _, _, raw_dim = config.load_sprite_configuration()
        sprite_dim = (
            raw_dim['w'], 
            raw_dim['h']
        )

        for set_key in list(apparel_conf.keys()):

            set_conf = apparel_conf[set_key]
            self.apparel[set_key] = {}

            for apparel_key, apparel in set_conf.items():
                self.apparel[set_key][apparel_key] = {}

                sheets = []
                for sheet in apparel['sheets']:
                    sheet_path = os.path.join(
                        ontology_path, 
                        *settings.APPAREL_PATH, 
                        sheet
                    )
                    sheet_img = Image.open(sheet_path).convert(settings.IMG_MODE)
                    sheets.append(sheet_img)

                if apparel['animate_states'] == 'all':
                    animate_states = list(states_conf['animate_states'].keys())
                else:
                    animate_states = apparel['animate_states']

                for equip_state in animate_states:
                    equip_state_conf = states_conf['animate_states'][equip_state]
                    equip_state_row = equip_state_conf['row']
                    equip_state_frames = equip_state_conf['frames']

                    start_y = equip_state_row * sprite_dim[1]
                    self.apparel[set_key][apparel_key][equip_state] = [] 

                    for i in range(equip_state_frames):
                        start_x = i*sprite_dim[0]
                        crop_box = (
                            start_x, 
                            start_y, 
                            start_x + sprite_dim[0], 
                            start_y + sprite_dim[1]
                        )
                        
                        crop_sheets = [
                            sheet.crop(crop_box) for sheet in sheets
                        ]
                    
                        equip_state_frame = gui.new_image(sprite_dim)

                        for sheet in crop_sheets:
                            equip_state_frame.paste(
                                sheet, 
                                (0,0), 
                                sheet
                            )

                        self.apparel[set_key][apparel_key][equip_state].append(equip_state_frame) 

    def _init_entity_assets(
        self, 
        config: conf.Conf, 
        ontology_path: str
    ) -> None:
        log.debug(
            'Initializing entity assets...', 
            'Repo._init_entity_assets'
        )

        states_conf, _, sheets_conf, raw_dim = config.load_sprite_configuration()
        sprite_dim = (
            raw_dim.w, 
            raw_dim.h
        )

        for sprite_key, sheet_conf in sheets_conf.items():
            accent_sheets = []
            self.sprite_bases[sprite_key] = {}
            self.sprite_accents[sprite_key] = {}

            base_path = os.path.join(
                ontology_path,
                *settings.SPRITE_BASE_PATH,
                sheet_conf.base
            )
            base_img = gui.open_image(
                base_path
            )

            if sheet_conf.get('accents'):
                for sheet in sheet_conf.accents:
                    sheet_path = os.path.join(
                        ontology_path, 
                        *settings.SPRITE_ACCENT_PATH, 
                        sheet
                    )
                    sheet_img = gui.open_image(
                        sheet_path
                    )
                    accent_sheets.append(
                        sheet_img
                    )
                
            frames = 0
            for state_key, state_conf in states_conf.animate_states.items():
                state_row, state_frames = (
                    state_conf.row, 
                    state_conf.frames
                )
                frames += state_frames

                self.sprite_bases[sprite_key][state_key] = []
                self.sprite_accents[sprite_key][state_key] = []

                start_y = state_row * sprite_dim[1]

                for i in range(state_frames):
                    start_x = i*sprite_dim[0]
                    crop_box = (
                        start_x, 
                        start_y, 
                        start_x + sprite_dim[0], 
                        start_y + sprite_dim[1]
                    )

                    sprite_base_frame = base_img.crop(crop_box)
                    
                    accent_crop_sheets = [ 
                        sheet.crop(crop_box) 
                        for sheet 
                        in accent_sheets 
                    ]
                
                    sprite_accent_frame = gui.new_image(sprite_dim)

                    for sheet in accent_crop_sheets:
                        sprite_accent_frame.paste(
                            sheet, 
                            (0,0), 
                            sheet
                        )

                    self.sprite_bases[sprite_key][state_key].append(
                        sprite_base_frame
                    )
                    self.sprite_accents[sprite_key][state_key].append(
                        sprite_accent_frame
                    )

            log.debug(
                f'{sprite_key} configuration: states - {len(self.sprite_bases[sprite_key])}, \
                frames - {frames}', 
                'Repo._init_entity_assets'
            )


    def get_form_frame(
        self, 
        form_key: str, 
        group_key: str
    ) -> Union[Image.Image, None]:
        if form_key in [ 'tiles', 'tile' ]:
            return self.tiles.get(group_key)
        if form_key in [ 'struts', 'strut' ]:
            return self.struts.get(group_key)
        if form_key in [ 'plates', 'plate' ]:
            return self.plates.get(group_key)
        return None


    def get_avatar_frame(
        self,
        avatar_set: str,
        component_key: str
    ) -> Union[Image.Image, None]:
        """_summary_

        :param component_key: _description_
        :type component_key: str
        :return: _description_
        :rtype: Union[Image.Image, None]
        """
        if self.avatars.get(avatar_set):
            return self.avatars[avatar_set].get(component_key)
        return None
    

    def get_slot_frames(
        self, 
        breakpoint_key: str, 
        component_key: str
    ) -> Union[Image.Image, None]:
        """_summary_

        :param breakpoint_key: _description_
        :type breakpoint_key: str
        :param component_key: _description_
        :type component_key: str
        :return: _description_
        :rtype: Union[Image.Image, None]
        """
        if self.slots.get(breakpoint_key):
            return self.slots[breakpoint_key].get(component_key)
        return None
        

    def get_pack_frame(
        self, 
        breakpoint_key: str, 
        component_key: str, 
        piece_key: str
    ) -> Union[Image.Image, None]:
        """_summary_

        :param breakpoint_key: _description_
        :type breakpoint_key: str
        :param component_key: _description_
        :type component_key: str
        :param piece_key: _description_
        :type piece_key: str
        :return: _description_
        :rtype: Union[Image.Image, None]
        """
        if self.packs.get(breakpoint_key) and \
            self.packs[breakpoint_key].get(component_key):
            return self.packs[breakpoint_key][component_key].get(piece_key)
        return None


    def get_mirror_frame(
        self, 
        breakpoint_key: str, 
        component_key: str, 
        frame_key: str
    ) -> Union[Image.Image, None]:
        """_summary_

        :param breakpoint_key: _description_
        :type breakpoint_key: str
        :param component_key: _description_
        :type component_key: str
        :param fill_key: _description_
        :type fill_key: str
        :return: _description_
        :rtype: Union[Image.Image, None]
        """
        if self.mirrors.get(breakpoint_key) and self.mirrors[breakpoint_key].get(component_key):
            return self.mirrors[breakpoint_key][component_key].get(frame_key)
        return None


    def get_menu_frame(
        self, 
        breakpoint_key: str, 
        component_key: str, 
        piece_key: str
    ) -> Union[Image.Image, None]:
        """_summary_

        :param breakpoint_key: _description_
        :type breakpoint_key: str
        :param component_key: _description_
        :type component_key: str
        :param piece_key: _description_
        :type piece_key: str
        :return: _description_
        :rtype: Union[Image.Image, None]
        """
        if self.menus.get(breakpoint_key) and self.menus[breakpoint_key].get(component_key):
            return self.menus[breakpoint_key][component_key].get(piece_key)
        return None


    def get_sprite_frame(
        self, 
        sprite_key: str, 
        state_key: str, 
        frame_index: int
    ) -> Union[tuple, None]:
        """Return the _Sprite frame corresponding to a given state and a frame iteration.

        :param sprite_key: _Sprite_ lookup key
        :type sprite_key: str
        :param state_key: State lookup key 
        :type state_key: str
        :param frame_index: Frame iteration lookup index; this variable represents which frame in the state animation the sprite is currently in.
        :type frame_index: int
        :return: An image representing the appropriate _Sprite_ state frame, or `None` if frame doesn't exist.
        :rtype: Union[Image.Image, None]
        """
        if (
                self.sprite_bases.get(sprite_key) and \
                    self.sprite_accents.get(sprite_key)
            ) and (
                self.sprite_bases[sprite_key].get(state_key) and \
                    self.sprite_accents[sprite_key].get(state_key)
            ):
                # TODO: check if frame index is less than state frames?
                return (
                    self.sprite_bases[sprite_key][state_key][frame_index],
                    self.sprite_accents[sprite_key][state_key][frame_index]
                )
        return (None, None)


    def get_apparel_frame(
        self,
        set_key: str,
        apparel_key: str,
        state_key: str,
        frame_index: int
    ) -> Union[Image.Image, None]:
        if self.apparel.get(set_key) and \
            self.apparel[set_key].get(apparel_key) and \
            self.apparel[set_key][apparel_key].get(state_key):
            # TODO: check if frame index is less than state frames?
            return self.apparel[set_key][apparel_key][state_key][frame_index]
        pass