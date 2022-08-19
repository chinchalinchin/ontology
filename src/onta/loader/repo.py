import os
import functools
from typing import Union

from PIL import Image
import munch

import onta.settings as settings
import onta.loader.conf as conf
import onta.engine.composition as composition
import onta.util.logger as logger
import onta.util.gui as gui


log = logger.Logger('onta.repo', settings.LOG_LEVEL)

# TODO: either a general typing.yaml or else each .yaml needs to specify types somehow.

STATIC_ASSETS_TYPES = [ 
    'tiles', 
    'struts', 
    'plates' 
]
SWITCH_PLATES_TYPES = [ 
    'container', 
    'pressure', 
    'gate' 
]
AVATAR_TYPES = [ 
    'armor', 
    'equipment', 
    'inventory', 
    'quantity' 
]
APPAREL_TYPES = [ 
    'armor', 
    'equipment' 
]
PIECEWISE_QUALIA_TYPES = [
    'mirror', 
    'pack', 
    'idea', 
    'bauble', 
    'aside', 
    'focus'
]
STYLED_QUALIA_TYPES = [ 
    'slot'
]
SIMPLE_QUALIA_TYPES=[
    'concept',
    'conception'
]
DIRECTIONAL_PIECE_DEFINTIONS = [
    'cap'
]
ALIGNMENT_PIECE_DEFINITIONS = [
    'buffer'
]



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
        return ( 90, 0, 180, 270 )
    elif direction == 'right':
        return ( 270, 180, 0, 90 )
    elif direction == 'up':
        return ( 0, 90,  270, 180 )
    return ( 180, 270, 90, 0 )


@functools.lru_cache(maxsize=2)
def adjust_alignment_rotation(
    direction: str
) -> tuple:
    if direction == 'vertical':
        return (0, 90)
    return (90, 0)

class Repo():

    # TODO: be careful with closures. 

    tiles = munch.Munch({})
    struts = munch.Munch({})
    plates = munch.Munch({})
    tracks = munch.Munch({})
    pixies = munch.Munch({})
    nymphs = munch.Munch({})
    sprites = munch.Munch({})
    avatars = munch.Munch({})
    expressions = munch.Munch({})
    projectiles = munch.Munch({})
    mirrors = munch.Munch({})
    qualia = munch.Munch({})
    # slots and packs are treated separately from other qualia since they are HUD.
    slots = munch.Munch({})
    packs = munch.Munch({})
    apparel = munch.Munch({})


    def __init__(
        self, 
        ontology_path: str
    ) -> None:
        """
        .. note::
            No reference is kept to `ontology_path`; it is passed to initialization methods and released.
        """
        config = conf.Conf(ontology_path)
        self._init_form_assets(config, ontology_path)
        self._init_entity_assets(config, ontology_path)
        self._init_apparel_assets(config, ontology_path)
        self._init_qualia_assets(config, ontology_path)
        self._init_avatar_assets(config, ontology_path)
        self._init_expression_assets(config, ontology_path)
        self._init_projectile_assets(config, ontology_path)


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
            log.debug(f'Initializing {asset_type} assets...',  '_init_form_assets')

            if asset_type == 'tiles':
                assets_conf = config.load_tile_configuration()
                w, h = assets_conf.tile.w, assets_conf.tile.h
            elif asset_type == 'struts':
                asset_props, assets_conf = config.load_strut_configuration()
            elif asset_type == 'plates':
                asset_props, assets_conf = config.load_plate_configuration()

            for asset_key, asset_conf in assets_conf.items():
                # need tile dimensions here...but tile dimensions don't exist until world
                # pulls static state...

                if asset_type != 'tiles':
                    w, h = asset_conf.size.w, asset_conf.size.h

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
                        x, y = asset_conf.position.x, asset_conf.position.y

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

                    buffer = gui.open_image(image_path)

                    log.debug(
                        f"{asset_key}: size - {buffer.size}, mode - {buffer.mode}", 
                        '_init_form_assets'
                    )

                    if asset_type == 'tiles':
                        setattr(
                            self.tiles,
                            asset_key,
                            buffer.crop(( x, y, w + x, h + y ))
                        )
                    elif asset_type == 'struts':
                        setattr(
                            self.struts,
                            asset_key,
                            buffer.crop(( x, y, w + x, h + y ))
                        )
                    elif asset_type == 'plates':
                        if asset_props.get(asset_key).get('type') in SWITCH_PLATES_TYPES:
                            setattr(
                                self.plates,
                                asset_key,
                                munch.Munch({
                                    'on': buffer.crop(( on_x, on_y, w + on_x, h + on_y )),
                                    'off': buffer.crop(( off_x, off_y, w + off_x, h + off_y ))
                                })
                            )
                        else:
                            setattr(
                                self.plates,
                                asset_key,
                                buffer.crop(( x, y, w + x, h + y ))
                            )
                        
                elif asset_conf.get('channels'):
                    channels = (
                        asset_conf.channels.r, 
                        asset_conf.channels.g,
                        asset_conf.channels.b,
                        asset_conf.channels.a
                    )
                    buffer = gui.channels(( w, h ), channels)

                    if asset_type == 'tiles':
                        setattr(self.tiles, asset_key, buffer)
                    elif asset_type == 'struts':
                        setattr(self.struts, asset_key, buffer)
                    elif asset_type == 'plates':
                        if asset_props.get(asset_key).get('type') in SWITCH_PLATES_TYPES:
                            setattr(
                                self.plates,
                                asset_key,
                                munch.Munch({ 'on': buffer, 'off': buffer})
                            )
                        else:
                            setattr(self.plates, asset_key, buffer)
 

    def _init_qualia_assets(
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
        log.debug(f'Initializing qualia assets...', '_init_qualia_assets')

        interface_conf = config.load_qualia_configuration()

        for size in interface_conf.sizes:

            if not self.slots.get(size):
                setattr(self.slots, size, munch.Munch({}))
            if not self.mirrors.get(size):
                setattr(self.mirrors, size, munch.Munch({}))
            if not self.packs.get(size):
                setattr(self.packs, size, munch.Munch({}))
            if not self.qualia.get(size):
                setattr(self.qualia, size, munch.Munch({}))


            ## STYLED INITIALIZATION
            for set_type in STYLED_QUALIA_TYPES:
                if set_type == 'slot':
                    iter_set = interface_conf.hud.get(size).slots
                    save_set = self.slots

                for set_key, set_conf in iter_set.items():
                    if not set_conf or not set_conf.get('path'):
                        continue

                    w, h = set_conf.size.w, set_conf.size.h   
                    x, y = set_conf.position.x, set_conf.position.y

                    buffer = gui.open_image(
                        os.path.join(
                            ontology_path,
                            *settings.QUALIA_PATH,
                            set_conf.path
                        )
                    )

                    log.debug( 
                        f"{size} {set_type} {set_key}: size - {buffer.size}, mode - {buffer.mode}", 
                        '_init_sense_assets'
                    )

                    buffer = buffer.crop(( x, y, w + x, h + y ))

                    if set_key in DIRECTIONAL_PIECE_DEFINTIONS:
                        adjust = adjust_directional_rotation(set_conf.definition)
                        setattr(
                            save_set.get(size),
                            set_key,
                            munch.Munch({
                                'down': buffer.rotate(adjust[0], expand=True),
                                'left': buffer.rotate(adjust[1], expand=True),
                                'right': buffer.rotate(adjust[2], expand=True),
                                'up': buffer.rotate(adjust[3], expand=True),
                            })
                        )
                        continue
                    elif set_key in ALIGNMENT_PIECE_DEFINITIONS:
                        adjust = adjust_alignment_rotation(set_conf.definition)
                        setattr(
                            save_set.get(size),
                            set_key,
                            munch.Munch({
                                'vertical': buffer.rotate(adjust[0], expand=True),
                                'horizontal': buffer.rotate(adjust[1], expand=True)
                            })
                        )
                        continue
                    setattr(self.slots.get(size), set_key, buffer)

            ## PIECEWISE DEFINITIONS
            for set_type in PIECEWISE_QUALIA_TYPES:
                # TODO: collapse this conditional into: iter_set = interface_conf.hud | menu.get(size).get(set_type)
                #           by defining and passing the proper literals...
                if set_type == 'mirror':
                    iter_set = interface_conf.hud.get(size).mirrors
                    save_set = self.mirrors
                elif set_type == 'pack':
                    iter_set = interface_conf.hud.get(size).packs
                    save_set = self.packs
                elif set_type == 'idea':
                    iter_set = interface_conf.menu.get(size).idea
                    save_set = self.qualia
                elif set_type == 'bauble':
                    iter_set = interface_conf.menu.get(size).bauble
                    save_set = self.qualia
                elif set_type == 'aside':
                    iter_set = interface_conf.menu.get(size).aside
                    save_set = self.qualia
                elif set_type == 'indicator':
                    iter_set = interface_conf.menu.get(size).focus
                    save_set = self.qualia
                    
                if set_type in [ 'bauble', 'thought', 'focus', 'aside' ]:
                    setattr(save_set.get(size), set_type, munch.Munch({}))

                # (enabled, conf), (disbled, conf), ...
                for set_key, set_conf in iter_set.items():
                    if not set_conf:
                        continue
                    
                    if set_type in [ 'bauble', 'thought', 'focus', 'aside' ]:
                        setattr(save_set.get(size).get(set_type), set_key, munch.Munch({}))
                    else: # HUD qualia ('mirror', 'pack')
                        setattr(save_set.get(size), set_key, munch.Munch({}))                        

                    # for (unit, fill), (empty, fill)
                    for component_key, component in set_conf.items():
                        if not component.get('path'):
                            continue

                        x, y = component.position.x, component.position.y
                        w, h = component.size.w, component.size.h
                        
                        buffer = gui.open_image(
                            os.path.join(
                                ontology_path,
                                *settings.QUALIA_PATH,
                                component.path
                            )
                        )

                        log.debug( 
                            f"{size} {set_type} {set_key} {component_key}: size - {buffer.size}, mode - {buffer.mode}", 
                            '_init_sense_assets'
                        )
                        if set_type in [ 'bauble', 'thought', 'focus', 'aside' ]:
                            setattr(
                                save_set.get(size).get(set_type).get(set_key),
                                component_key,
                                buffer.crop(( x, y, w + x, h + y))
                            )
                        else: # HUD qualia ('mirror', 'pack')
                            setattr(
                                save_set.get(size).get(set_key),
                                component_key,
                                buffer.crop(( x, y, w + x, h + y))
                            )
            
            ## SIMPLE DEFINITIONS
            for set_type in SIMPLE_QUALIA_TYPES:
                if set_type == 'concept':
                    simple_set = interface_conf.menu.get(size).concept

                elif set_type == 'conception':
                    simple_set = interface_conf.menu.get(size).conception

                if not simple_set.get('path'):
                    continue
            
                x, y = simple_set.position.x, simple_set.position.y
                w, h = simple_set.size.w, simple_set.size.h

                # simple qualia need to be stored and retrieved dirrecently if doing it this way.


    def _init_projectile_assets(
        self,
        config: conf.Conf,
        ontology_path: str
    ) -> None:
        _, projectile_conf = config.load_projectile_configuration()

        for project_key, projectile in projectile_conf.items():
            if not projectile or not projectile.get('path'):
                continue
            x,y = ( projectile.position.x, projectile.position.y )
            w, h = ( projectile.size.w, projectile.size.h )
            buffer = gui.open_image(
                os.path.join(
                    ontology_path,
                    *settings.PROJECTILE_PATH,
                    projectile.path
                )
            )

            buffer.crop(( x, y, w + x, h + y ))

            adjust = adjust_directional_rotation(projectile.definition)
            setattr(
                self.projectiles,
                project_key,
                munch.Munch({
                    'down': buffer.rotate(adjust[0], expand=True),
                    'left': buffer.rotate(adjust[1], expand=True),
                    'right': buffer.rotate(adjust[2], expand=True),
                    'up': buffer.rotate(adjust[3], expand=True),
                })
            )


    def _init_expression_assets(
        self,
        config: conf.Conf,
        ontology_path: str
    ) -> None:
        expression_conf = config.load_expression_configuration()

        for express_key, expression in expression_conf.items():
            if not expression or not expression.get('path'):
                continue
            x,y = ( expression.position.x, expression.position.y )
            w, h = ( expression.size.w, expression.size.h )
            buffer = gui.open_image(
                os.path.join(
                    ontology_path,
                    *settings.EXPRESSION_PATH,
                    expression.path
                )
            )
            setattr(
                self.expressions,
                express_key,
                buffer.crop(( x, y, x + w, y + h))
            )


    def _init_avatar_assets(
        self, 
        config: conf.Conf, 
        ontology_path: str
    ) -> None:
        avatar_conf = config.load_avatar_configuration()

        for avatarset_key in AVATAR_TYPES:
            setattr(self.avatars, avatarset_key, munch.Munch({}))

            for avatar_key, avatar in avatar_conf.avatars.get(avatarset_key).items():
                if not avatar or not avatar.get('path'):
                    continue

                x,y = ( avatar.position.x, avatar.position.y )
                w,h = ( avatar.size.w, avatar.size.h )
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
                    buffer.crop(( x, y, w + x, h + y ))
                )


    def _init_apparel_assets(
        self,
        config: conf.Conf,
        ontology_path: str
    ) -> None:


        apparel_conf = config.load_apparel_configuration()
        stature, _, _, sprite_dim = config.load_sprite_configuration()

        for set_key, set_conf in apparel_conf.items():
            setattr(self.apparel, set_key, munch.Munch({}))

            for apparel_key, apparel in set_conf.items():
                setattr(
                    self.apparel.get(set_key),
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
                    animate_statures = composition.construct_animate_statures(stature)

                else:
                    animate_statures = apparel.animate_statures

                for equip_stature in animate_statures:
                    equip_stature_conf = stature.animate_map.get(equip_stature)
                    equip_stature_row = equip_stature_conf.row
                    equip_stature_frames = equip_stature_conf.frames

                    start_y = equip_stature_row * sprite_dim[1]

                    setattr(
                        self.apparel.get(set_key).get(apparel_key),
                        equip_stature,
                        []
                    )

                    for i in range(equip_stature_frames):
                        start_x = i*sprite_dim[0]
                        crop_box = (
                            start_x, 
                            start_y, 
                            start_x + sprite_dim[0], 
                            start_y + sprite_dim[1]
                        )
                        
                        crop_sheets = [ sheet.crop(crop_box) for sheet in sheets ]
                    
                        equip_stature_frame = gui.new_image(sprite_dim)

                        for sheet in crop_sheets:
                            equip_stature_frame.paste(sheet, ( 0,0 ), sheet)

                        self.apparel.get(set_key).get(apparel_key).get(equip_stature
                        ).append(equip_stature_frame) 


    def _init_entity_assets(
        self, 
        config: conf.Conf, 
        ontology_path: str
    ) -> None:
        log.debug('Initializing entity assets...', '_init_entity_assets')

        stature_conf, _, sheets_conf, sprite_dim = config.load_sprite_configuration()

        setattr(self.sprites, 'base', munch.Munch({}))
        setattr(self.sprites, 'accents', munch.Munch({}))

        for sprite_key, sheet_conf in sheets_conf.items():
            setattr(self.sprites.base, sprite_key, munch.Munch({}))
            setattr(self.sprites.accents, sprite_key, munch.Munch({}))
            accent_sheets = []

            base_img = gui.open_image(
                os.path.join(
                    ontology_path,
                    *settings.SPRITE_BASE_PATH,
                    sheet_conf.base
                )
            )

            if sheet_conf.get('accents'):
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
                    self.sprites.base.get(sprite_key),
                    stature_key,
                    []
                )
                setattr(
                    self.sprites.accents.get(sprite_key),
                    stature_key,
                    []
                )
                start_y = stature.row * sprite_dim[1]

                for i in range(stature.frames):
                    start_x = i*sprite_dim[0]
                    crop_box = (
                        start_x, 
                        start_y, 
                        start_x + sprite_dim[0], 
                        start_y + sprite_dim[1]
                    )

                    sprite_base_frame = base_img.crop(crop_box)
                    
                    accent_crop_sheets = [ 
                        sheet.crop(crop_box) for sheet in accent_sheets 
                    ]
                
                    sprite_accent_frame = gui.new_image(sprite_dim)

                    for sheet in accent_crop_sheets:
                        sprite_accent_frame.paste(sheet, ( 0,0 ), sheet)

                    self.sprites.base.get(sprite_key).get(stature_key).append(
                        sprite_base_frame
                    )
                    self.sprites.accents.get(sprite_key).get(stature_key).append(
                        sprite_accent_frame
                    )

            log.debug(
                f'{sprite_key}: states - {len(self.sprites.base.get(sprite_key))}, frames - {frames}', 
                '_init_entity_assets'
            )


    @functools.lru_cache(maxsize=48)
    def get_projectile_frame(
        self,
        project_key,
        project_direction
    ) -> Union[Image.Image, None]:
        if self.projectiles.get(project_key):
            return self.projectiles.get(project_key).get(project_direction)
        return None


    @functools.lru_cache(maxsize=20)
    def get_expression_frame(
        self,
        express_key
    ) -> Union[Image.Image, None]:
        return self.expressions.get(express_key)


    @functools.lru_cache(maxsize=128)
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


    @functools.lru_cache(maxsize=64)
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
            return self.avatars.get(avatar_set).get(component_key)
        return None
    

    @functools.lru_cache(maxsize=8)
    def get_slot_frames(
        self, 
        breakpoint_key: str, 
        component_key: str
    ) -> Union[munch.Munch, None]:
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
            self.packs.get(breakpoint_key).get(component_key):
            return self.packs.get(breakpoint_key).get(component_key).get(piece_key)
        return None


    @functools.lru_cache(maxsize=8)
    def get_mirror_frame(
        self, 
        breakpoint_key: str, 
        component_key: str, 
        fill_key: str
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
        if self.mirrors.get(breakpoint_key) and \
            self.mirrors.get(breakpoint_key).get(component_key):
            return self.mirrors.get(breakpoint_key).get(component_key).get(fill_key)
        return None


    @functools.lru_cache(maxsize=64)
    def get_piecewise_qualia_frame(
        self, 
        breakpoint_key: str, 
        component_key: str, 
        status_key: str,
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
        if self.qualia.get(breakpoint_key) and \
            self.qualia.get(breakpoint_key).get(component_key) and \
            self.qualia.get(breakpoint_key).get(component_key).get(status_key):

            return self.qualia.get(breakpoint_key).get(component_key).get(
                status_key).get(piece_key)
        return None


    @functools.lru_cache(maxsize=64)
    def get_simple_qualia_frame(
        self,
        breakpoint_key,
        component_key
    ) -> Union[Image.Image, None]:
        if self.qualia.get(breakpoint_key):
            return self.qualia.get(breakpoint_key).get(component_key)
        return None


    @functools.lru_cache(maxsize=1024)
    def get_sprite_frame(
        self, 
        sprite_key: str, 
        stature_key: str, 
        frame_index: int
    ) -> Union[tuple, None]:
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
        if self.sprites.base.get(sprite_key) and \
            self.sprites.accents.get(sprite_key) and \
            self.sprites.base.get(sprite_key).get(stature_key) and \
            self.sprites.accents.get(sprite_key).get(stature_key):

                # TODO: check if frame index is less than state frames?
                return (
                    self.sprites.base.get(sprite_key).get(stature_key)[frame_index],
                    self.sprites.accents.get(sprite_key).get(stature_key)[frame_index]
                )
        elif self.sprites.base.get(sprite_key) and \
            self.sprites.base.get(sprite_key).get(stature_key):
            return (
                self.sprites.bases.get(sprite_key).get(stature_key)[frame_index],
                None
            )
        return (None, None)


    @functools.lru_cache(maxsize=1024)
    def get_apparel_frame(
        self,
        set_key: str,
        apparel_key: str,
        state_key: str,
        frame_index: int
    ) -> Union[Image.Image, None]:
        if self.apparel.get(set_key) and \
            self.apparel.get(set_key).get(apparel_key) and \
            self.apparel.get(set_key).get(apparel_key).get(state_key):
            # TODO: check if frame index is less than state frames?
            return self.apparel.get(set_key).get(apparel_key).get(state_key)[frame_index]
        return None