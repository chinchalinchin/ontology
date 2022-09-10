import functools
import munch
import os
from typing \
    import Union
from PIL \
    import Image

from onta.actuality \
    import conf
from onta.concretion \
    import composition
from onta.metaphysics \
    import settings, logger, gui, constants


log = logger.Logger(
    'onta.actuality.datum', 
    settings.LOG_LEVEL
)

class Totality():
    @staticmethod
    @functools.lru_cache(maxsize=2)
    def adjust_alignment_rotation(
        direction: str
    ) -> tuple:
        if direction == 'vertical':
            return ( 
                0, 
                90 
            )
        return ( 
            90, 
            0 
        )

    @staticmethod
    @functools.lru_cache(maxsize=4)
    def adjust_directional_rotation(
        direction: str
    ) -> tuple:
        """Static method to calculate the amount of rotation necessary to align slot cap with style alignment, depending on which direction the slot cap was defined in, i.e. if the slot cap was extracted from the asset file pointing to the left, this same piece can be rotated and reused, rather than extracting multiple assets.

        :param direction: The direction of the slot cap direction.
        :type direction: str
        :return: (up_adjust, left_adjust, right_adjust, down_adjust)
        :rtype: tuple
        """
        # I am convinced there is an easier way to calculate this using arcosine and arcsine,
        # but i don't feel like thinking about domains and ranges right now...
        if direction == 'left':
            return ( 
                90, 
                0, 
                180, 
                270 
            )
        elif direction == 'right':
            return ( 
                270, 
                180, 
                0, 
                90 
            )
        elif direction == 'up':
            return ( 
                0, 
                90,  
                270, 
                180 
            )
        return ( 
            180, 
            270, 
            90, 
            0 
        )

    @staticmethod
    @functools.lru_cache(maxsize=4)
    def map_form_path(
        asset_type
    ) -> Union[
        list, 
        None
    ]:
        if asset_type == constants.FormType.TILE.value:
            return settings.TILE_PATH
        if asset_type == constants.FormType.STRUT.value:
            return settings.STRUT_PATH
        if asset_type == constants.FormType.PLATE.value: 
            return settings.PLATE_PATH    
        return None

    @staticmethod
    @functools.lru_cache(maxsize=3)
    def map_dialectic_path(
        asset_type
    ) -> Union[
        list, 
        None
    ]:
        if asset_type == 'projectiles':
            return settings.PROJECTILE_PATH
        if asset_type == 'expressions':
            return settings.EXPRESSION_PATH
        return None


    def __init__(
        self, 
        ontology_path: str = settings.DEFAULT_DIR
    ) -> None:
        """
        .. note::
            No reference is kept to `ontology_path`; it is passed to initialization methods and released.
        """
        config = conf.Conf(ontology_path)
        self._init_fields()
        self._init_form_assets(
            config, 
            ontology_path
        )
        self._init_entity_assets(
            config, 
            ontology_path
        )
        self._init_self_assets(
            config, 
            ontology_path
        )
        self._init_dialectic_assets(
            config, 
            ontology_path
        )


    def _init_fields(
        self
    ) -> None:
        """
        
        .. note::
            ```python
            self.forms = {
                'tiles': { ... },
                'struts': { ... },
                'plates': { ... },
                'tracks': { ... },
            }
            self.entities = {
                'pixies': { ... },
                'nymphs': { ... },
                'sprites': { ... },
            }
            self.selves = {
                'avatars': { ... },
                'qualia': { ... },
            }
            self.dialectices = {
                'expressions': { ... },
                'projectiles': { ... },
                'portraits': { ... },
            }
            ```
        """
        self.forms = munch.Munch({})
        self.entities = munch.Munch({})
        self.selves = munch.Munch({})
        self.dialectics = munch.Munch({})


    def _init_form_assets(
        self, config: 
        conf.Conf, 
        ontology_path: str
    ) -> None:
        """_summary_

        :param config: Configuration class initialized with the file path.
        :type config: conf.Conf
        :param ontology_path: Root file path.
        :type ontology_path: str

        .. note::
            - Static assets, i.e. _Tile_\s, _Strut_\s & _Plate_\s can be rendered using RGBA channels instead of cropping a sheet file into an PIL image. If the channels are specified through the configuration file for the appropriate _Form_ asset, the asset frame will be created using through channels. Particularly useful if you need to create an inside door with a transculent light square leading back outside.
        """

        for asset_type in list(
            e.value 
            for e 
            in constants.FormType.__members__.values()
            if e.value != constants.FormType.COMPOSITE.value
        ):
            log.debug(
                f'Initializing {asset_type} assets...',  
                'Totality._init_form_assets'
            )

            setattr(
                self.forms, 
                asset_type, 
                munch.Munch({})
            )
            asset_props, assets_conf = \
                config.load_form_configuration(asset_type)

            if asset_type == constants.FormType.TILE.value:
                # NOTE: all tile types are the same size...
                w, h = assets_conf.size.w, assets_conf.size.h 

            for asset_key, asset_conf in assets_conf.items():
                log.verbose(
                    f'Initializing {asset_key}...',
                    'Totality._init_form_assets'
                )
                if asset_type != constants.FormType.TILE.value:
                    # NOTE: ...but all other form sizes are dependent on type
                    w, h = asset_conf.size.w, asset_conf.size.h

                if asset_conf.get('path'):
                    # NOTE: if defining form through image file...

                    form_type_path = self.map_form_path(asset_type)
                    if not form_type_path:
                        continue 

                    buffer = gui.open_image(
                        os.path.join(
                            ontology_path, 
                            *form_type_path, 
                            asset_conf.path
                        )
                    )

                    log.verbose(
                        f"{asset_key}: size - {buffer.size}, mode - {buffer.mode}", 
                        'Totality._init_form_assets'
                    )

                    if asset_props and \
                        asset_props.get(asset_key).get('type') in list(
                            e.value 
                            for e 
                            in constants.SwitchPlateType.__members__.values()
                        ):

                        setattr(
                            self.forms.get(asset_type),
                            asset_key,
                            munch.Munch({
                                'on': buffer.crop(
                                    ( 
                                        asset_conf.position.on_position.x,
                                        asset_conf.position.on_position.y, 
                                        w + asset_conf.position.on_position.x, 
                                        h + asset_conf.position.on_position.y 
                                    )
                                ),
                                'off': buffer.crop(
                                    ( 
                                        asset_conf.position.off_position.x, 
                                        asset_conf.position.off_position.y, 
                                        w + asset_conf.position.off_position.x,
                                        h + asset_conf.position.off_position.y
                                    )
                                )
                            })
                        )
                        continue

                    setattr(
                        self.forms.get(asset_type),
                        asset_key,
                        buffer.crop(
                            ( 
                                asset_conf.position.x, 
                                asset_conf.position.y, 
                                w + asset_conf.position.x, 
                                h + asset_conf.position.y
                            )
                        )
                    )
                    continue
                        
                elif asset_conf.get('channels'):
                    # NOTE: ...else if defining form through (R,G,B) channels...

                    channels = (
                        asset_conf.channels.r, 
                        asset_conf.channels.g,
                        asset_conf.channels.b,
                        asset_conf.channels.a
                    )

                    buffer = gui.channels(
                        ( w, h ), 
                        channels
                    )

                    if asset_props.get(asset_key).get('type') in list(
                        e.value 
                        for e
                        in constants.SwitchPlateType.__members__.values()
                    ):
                        setattr(
                            self.forms.get(asset_type),
                            asset_key,
                            munch.Munch({ 
                                'on': buffer, 
                                'off': buffer
                            })
                        )
                        continue

                    setattr(
                        self.forms.get(asset_type), 
                        asset_key, 
                        buffer
                    )


    def _init_dialectic_assets(
        self,
        config: conf.Conf,
        ontology_path: str
    ) -> None:

        for asset_type in list(
            e.value 
            for e 
            in constants.DialecticType.__members__.values()
        ):
            log.debug(
                f'{asset_type} initialization',
                'Totality._init_dialectic_assets'
            )

            setattr(
                self.dialectics, 
                asset_type, 
                munch.Munch({})
            )

            _, assets_conf = \
                config.load_dialectic_configuration(asset_type)

            for asset_key, asset_conf in assets_conf.items():
                log.verbose(
                    f'Initializing {asset_key} assets...',
                    'Totality._init_dialectic_assets'
                )

                if not asset_conf or not asset_conf.get('path'):
                    continue

                dialectic_type_path = self.map_dialectic_path(asset_type)
                if not dialectic_type_path:
                    continue

                buffer = gui.open_image(
                    os.path.join(
                        ontology_path,
                        *dialectic_type_path,
                        asset_conf.path
                    )
                )

                buffer = buffer.crop(
                    ( 
                        asset_conf.position.x, 
                        asset_conf.position.y, 
                        asset_conf.size.w + asset_conf.position.x, 
                        asset_conf.size.h + asset_conf.position.y
                    )
                )

                if asset_type == constants.DialecticType.PROJECTILE.value:

                    adjust = self.adjust_directional_rotation(asset_conf.definition)

                    setattr(
                        self.dialectics.get(asset_type),
                        asset_key,
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
                    continue
                
                # else asset_type == 'expression'
                setattr(
                    self.dialectics.get(asset_type),
                    asset_key,
                    buffer
                )


    def _init_self_assets(
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
        # NOTE: avatar and qualia data structures are too different to condense initialization into one loop, 
        #       which begs the questions, should they be grouped into the same hierarchical type?


        log.debug(
            f'Initializing avatar assets...', 
            'Totality._init_qualia_assets'
        )

        setattr(
            self.selves,
            constants.SelfType.AVATAR.value,
            munch.Munch({})
        )

        avatar_conf = config.load_avatar_configuration()

        for avatarset_key, avatarset_conf in avatar_conf.items():
            setattr(
                self.avatars, 
                avatarset_key, 
                munch.Munch({})
            )

            for avatar_key, avatar in avatarset_conf.items():
                if not avatar or not avatar.get('path'):
                    continue

                buffer = gui.open_image(
                    os.path.join(
                        ontology_path,
                        *settings.AVATAR_PATH,
                        avatar.path
                    )
                )
                setattr(
                    self.avatars.get(avatarset_key),
                    avatar_key,
                    buffer.crop(
                        ( 
                            avatar.position.x, 
                            avatar.position.y , 
                            avatar.size.w + avatar.position.x, 
                            avatar.size.h + avatar.position.y 
                        )
                    )
                )

        log.debug(
            f'Initializing qualia assets...', 
            'Totality._init_self_assets'
        )

        setattr(
            self.selves,
            constants.SelfType.QUALIA.value,
            munch.Munch({})
        )

        qualia_conf = config.load_qualia_configuration().qualia

        for size, quale_families in qualia_conf.items():
            setattr(
                self.selves.get(constants.SelfType.QUALIA.value),
                size,
                munch.Munch({})
            )

            # (extrinsic, conf), (intrinsic, conf), ...
            for family, definition in quale_families.items():
                setattr(
                    self.selves.get(constants.SelfType.QUALIA.value).get(size),
                    family,
                    munch.Munch({})
                )

                # (simple, conf), (fillable, conf)....
                for def_type, quales in definition.items():

                    # NOTE: dependent on the quale family and def_type
                    #       e.g., (wallet, conf), (cap, conf), (buffer, conf), ..
                    #       or     (bag, conf), (belt, conf)
                    for quale_key, quale_conf in quales.items():

                        if def_type == 'simple':
                            if not quale_conf or not quale_conf.get('path'):
                                continue

                            buffer = gui.open_image(
                                os.path.join(
                                    ontology_path,
                                    *settings.QUALIA_PATH,
                                    quale_conf.path
                                )
                            )

                            log.debug( 
                                f"{size} {family} {quale_key}: size - {buffer.size}, mode - {buffer.mode}", 
                                'Totality._init_self_assets'
                            )

                            buffer = buffer.crop(
                                ( 
                                    quale_conf.position.x, 
                                    quale_conf.position.y, 
                                    quale_conf.size.w + quale_conf.position.x, 
                                    quale_conf.size.h + quale_conf.position.y 
                                )
                            )

                            setattr(
                                self.selves.get(constants.SelfType.QUALIA.value).get(size).get(family),
                                quale_key,
                                buffer
                            )
                            
                        elif def_type == 'rotatable':
                            if not quale_conf or not quale_conf.get('path'):
                                continue

                            buffer = gui.open_image(
                                os.path.join(
                                    ontology_path,
                                    *settings.QUALIA_PATH,
                                    quale_conf.path
                                )
                            )

                            log.debug( 
                                f"{size} {family} {quale_key}: size - {buffer.size}, mode - {buffer.mode}", 
                                'Totality._init_self_assets'
                            )

                            buffer = buffer.crop(
                                ( 
                                    quale_conf.position.x, 
                                    quale_conf.position.y, 
                                    quale_conf.size.w + quale_conf.position.x, 
                                    quale_conf.size.h + quale_conf.position.y 
                                )
                            )

                            if quale_conf.get('rotation') == 'directional':
                                adjust = self.adjust_directional_rotation(quale_conf.definition)
                                buffer = munch.Munch({
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
                            elif quale_conf.get('rotation') == 'alignment':
                                adjust = self.adjust_alignment_rotation(quale_conf.definition)
                                buffer = munch.Munch({
                                    'vertical': buffer.rotate(
                                        adjust[0], 
                                        expand=True
                                    ),
                                    'horizontal': buffer.rotate(
                                        adjust[1], 
                                        expand=True
                                    )
                                })
                        
                            setattr(
                                self.selves.get(constants.SelfType.QUALIA.value).get(size).get(family),
                                quale_key,
                                buffer
                            )

                        elif def_type == 'fillable':
                            pass
                        elif def_type == 'traversable':
                            pass
                        elif def_type == 'piecewise':
                            pass
                        elif def_type == 'piecewise_traversable':
                            pass


    def _init_entity_assets(
        self, 
        config: conf.Conf, 
        ontology_path: str
    ) -> None:

        ## BASE AND ACCENT INITIALIZATION
        log.debug(
            'Initializing base spritesheets...', 
            'Totality._init_entity_assets'
        )
        stature_conf, _, sheets_conf, sprite_dim = \
            config.load_sprite_configuration()

        setattr(
            self.entities, 
            'sprites', 
            munch.Munch({
                'base': munch.Munch({}),
                'accents': munch.Munch({})
            })
        )

        for sprite_key, sheet_conf in sheets_conf.items():
            log.verbose(
                f'Initializing {sprite_key} base sheet...',
                'Totality._init_entity_assets'
            )

            setattr(
                self.entities.sprites.base, 
                sprite_key, 
                munch.Munch({})
            )
            setattr(
                self.entities.sprites.accents, 
                sprite_key, 
                munch.Munch({})
            )

            accent_sheets = []

            base_img = gui.open_image(
                os.path.join(
                    ontology_path,
                    *settings.SPRITE_BASE_PATH,
                    sheet_conf.base
                )
            )

            if sheet_conf.get('accents'):
                log.verbose(
                    f'Initializing {sprite_key} accent sheets...',
                    'Totality._init_entity_assets'
                )

                for sheet in sheet_conf.accents:
                    accent_sheets.append(
                        gui.open_image(
                            os.path.join(
                                ontology_path, 
                                *settings.SPRITE_ACCENT_PATH, 
                                sheet
                            )
                        )
                    )
                
            frames = 0
            for stature_key, stature in stature_conf.animate_map.items():
                frames += stature.frames

                setattr(
                    self.entities.sprites.base.get(sprite_key),
                    stature_key,
                    []
                )
                setattr(
                    self.entities.sprites.accents.get(sprite_key),
                    stature_key,
                    []
                )

                for i in range(stature.frames):
                    crop_box = (
                        i * sprite_dim[0], 
                        stature.row * sprite_dim[1], 
                        ( i + 1 ) * sprite_dim[0] , 
                        ( stature.row + 1 ) * sprite_dim[1]
                    )

                    sprite_base_frame = base_img.crop(crop_box)
                    
                    accent_crop_sheets = [ 
                        sheet.crop(crop_box) for sheet in accent_sheets 
                    ]
                
                    sprite_accent_frame = gui.new_image(sprite_dim)

                    for sheet in accent_crop_sheets:
                        sprite_accent_frame.paste(
                            sheet, 
                            ( 0,0 ), 
                            sheet
                        )

                    self.entities.sprites.base.get(sprite_key).get(stature_key).append(
                        sprite_base_frame
                    )
                    self.entities.sprites.accents.get(sprite_key).get(stature_key).append(
                        sprite_accent_frame
                    )

            log.debug(
                f'{sprite_key}: states - {len(self.entities.sprites.base.get(sprite_key))}, frames - {frames}', 
                'Totality._init_entity_assets'
            )

        ## APPAREL INITIALIZATION
        log.debug(
            'Initializing apparel sheets...',
            'Totality._init_entity_assets'
        )
        apparel_conf = config.load_apparel_configuration()
        setattr(
            self.entities, 
            'apparel', 
            munch.Munch({})
        )

        for set_key, set_conf in apparel_conf.items():
            setattr(
                self.entities.apparel, 
                set_key, 
                munch.Munch({})
            )

            for apparel_key, apparel in set_conf.items():
                log.verbose(
                    f'Initializing {set_key} {apparel_key} apparel...',
                    'Totality._init_entity_assets'
                )
                
                setattr(
                    self.entities.apparel.get(set_key),
                    apparel_key,
                    munch.Munch({})
                )

                sheets = []
                for sheet in apparel.sheets:
                    sheets.append(
                        gui.open_image(
                            os.path.join(
                                ontology_path, 
                                *settings.SPRITE_APPAREL_PATH, 
                                sheet
                            )
                        )
                    )

                if apparel.animate_statures == 'all':
                    animate_statures = composition.construct_animate_statures(stature_conf)

                else:
                    animate_statures = apparel.animate_statures

                for equip_stature in animate_statures:
                    setattr(
                        self.entities.apparel.get(set_key).get(apparel_key),
                        equip_stature,
                        []
                    )

                    for i in range(stature_conf.animate_map.get(equip_stature).frames):
                        crop_box = (
                            i * sprite_dim[0], 
                            stature_conf.animate_map.get(equip_stature).row * sprite_dim[1], 
                            ( i + 1 ) * sprite_dim[0], 
                            ( stature_conf.animate_map.get(equip_stature).row + 1 ) * sprite_dim[1]
                        )
                        
                        crop_sheets = [ 
                            sheet.crop(crop_box) 
                            for sheet 
                            in sheets 
                        ]
                    
                        equip_stature_frame = gui.new_image(sprite_dim)

                        for sheet in crop_sheets:
                            equip_stature_frame.paste(
                                sheet, 
                                ( 0,0 ), 
                                sheet
                            )

                        self.entities.apparel.get(set_key).get(apparel_key).get(equip_stature
                            ).append(equip_stature_frame) 


    @functools.lru_cache(maxsize=48)
    def get_projectile_frame(
        self,
        project_key,
        project_direction
    ) -> Union[
        Image.Image, 
        None
    ]:
        if self.dialectics.projectiles.get(project_key):
            return self.dialectics.projectiles.get(project_key).get(project_direction)
        return None


    @functools.lru_cache(maxsize=20)
    def get_expression_frame(
        self,
        express_key
    ) -> Union[
        Image.Image, 
        None
    ]:
        return self.dialectics.expressions.get(express_key)


    @functools.lru_cache(maxsize=256)
    def get_form_frame(
        self, 
        form_key: str, 
        group_key: str
    ) -> Union[
        Image.Image, 
        None
    ]:
        if self.forms.get(form_key):
            return self.forms.get(form_key).get(group_key)
        return None


    @functools.lru_cache(maxsize=64)
    def get_avatar_frame(
        self,
        avatarset_key: str,
        avatar_key: str
    ) -> Union[
        Image.Image, 
        None
    ]:
        """Retrieve an _Avatar_ frame.

        :param avatarset_key: `equipment | armory | inventory | quantity`
        :type avatarset_key: str
        :param avatar_key: The avatar key under the set to retrieve.
        :type avatar_key: str
        :return: _Avatar_ frame image.
        :rtype: Union[Image.Image, None]
        """
        if self.avatars.get(avatarset_key):
            return self.avatars.get(avatarset_key).get(avatar_key)
        return None
    

    @functools.lru_cache(maxsize=8)
    def get_slot_frames(
        self, 
        breakpoint_key: str, 
        component_key: str
    ) -> Union[
        munch.Munch, 
        None
    ]:
        """_summary_

        :param breakpoint_key: _description_
        :type breakpoint_key: str
        :param component_key: _description_
        :type component_key: str
        :return: _description_
        :rtype: Union[Image.Image, None]
        """
        if self.slots.get(breakpoint_key):
            return self.slots.get(breakpoint_key).get(component_key)
        return None
        

    @functools.lru_cache(maxsize=8)
    def get_pack_frame(
        self, 
        breakpoint_key: str, 
        component_key: str, 
        piece_key: str
    ) -> Union[
        Image.Image, 
        None
    ]:
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
        print(self.packs)
        if self.packs.get(breakpoint_key) and \
            self.packs.get(breakpoint_key).get(component_key):
            return self.packs.get(breakpoint_key).get(component_key).get(piece_key)
        return None


    @functools.lru_cache(maxsize=8)
    def get_mirror_frame(
        self, 
        breakpoint_key: str, 
        component_key: str, 
        fill_key: str
    ) -> Union[
        Image.Image, 
        None
    ]:
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
        if self.mirrors.get(breakpoint_key) and \
            self.mirrors.get(breakpoint_key).get(component_key):
            return self.mirrors.get(breakpoint_key).get(component_key).get(fill_key)
        return None


    @functools.lru_cache(maxsize=64)
    def get_piecewise_qualia_frame(
        self, 
        breakpoint_key: str, 
        component_key: str, 
        frame_key: str,
        piece_key: str
    ) -> Union[
        Image.Image, 
        None
    ]:
        """_summary_

        :param breakpoint_key: _description_
        :type breakpoint_key: str
        :param component_key: _description_
        :type component_key: str
        :param frame_key: _description_
        :type frame_key: str
        :param piece_key: _description_
        :type piece_key: str
        :return: _description_
        :rtype: Union[Image.Image, None]
        """
        if self.qualia.get(breakpoint_key) and \
            self.qualia.get(breakpoint_key).get(component_key) and \
            self.qualia.get(breakpoint_key).get(component_key).get(frame_key):

            return self.qualia.get(breakpoint_key).get(component_key).get(
                frame_key).get(piece_key)
        return None


    @functools.lru_cache(maxsize=64)
    def get_simple_qualia_frame(
        self,
        breakpoint_key,
        component_key
    ) -> Union[
        Image.Image, 
        None
    ]:
        if self.qualia.get(breakpoint_key):
            return self.qualia.get(breakpoint_key).get(component_key)
        return None


    @functools.lru_cache(maxsize=1024)
    def get_sprite_frame(
        self, 
        sprite_key: str, 
        stature_key: str, 
        frame_index: int
    ) -> Union[
        tuple, 
        None
    ]:
        """Return the _Sprite frame corresponding to a given state and a frame iteration.

        :param sprite_key: _Sprite_ lookup key
        :type sprite_key: str
        :param stature_key: State lookup key 
        :type stature_key: str
        :param frame_index: Frame iteration lookup index; this variable represents which frame in the state animation the sprite is currently in.
        :type frame_index: int
        :return: An image representing the appropriate _Sprite_ state frame, or `None` if frame doesn't exist.
        :rtype: Union[Image.Image, None]
        """
        if self.entities.sprites.base.get(sprite_key) and \
            self.entities.sprites.accents.get(sprite_key) and \
            self.entities.sprites.base.get(sprite_key).get(stature_key) and \
            self.entities.sprites.accents.get(sprite_key).get(stature_key):

                # TODO: check if frame index is less than state frames?
                return (
                    self.entities.sprites.base.get(sprite_key).get(stature_key)[frame_index],
                    self.entities.sprites.accents.get(sprite_key).get(stature_key)[frame_index]
                )
        elif self.entities.sprites.base.get(sprite_key) and \
            self.entities.sprites.base.get(sprite_key).get(stature_key):
            return (
                self.entities.sprites.bases.get(sprite_key).get(stature_key)[frame_index],
                None
            )
        return (
            None, 
            None
        )


    @functools.lru_cache(maxsize=1024)
    def get_apparel_frame(
        self,
        set_key: str,
        apparel_key: str,
        stature_key: str,
        frame_index: int
    ) -> Union[
        Image.Image, 
        None
    ]:
        if self.entities.apparel.get(set_key) and \
            self.entities.apparel.get(set_key).get(apparel_key) and \
            self.entities.apparel.get(set_key).get(apparel_key).get(stature_key):
            # TODO: check if frame index is less than state frames?
            return self.entities.apparel.get(set_key).get(apparel_key).get(stature_key)[frame_index]
        return None