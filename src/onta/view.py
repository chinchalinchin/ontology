import sys
from collections import OrderedDict

import munch

from PySide6 import QtWidgets, QtGui
from PIL import Image

import onta.device as device
import onta.settings as settings
import onta.world as world

import onta.engine.senses.hud as hud
import onta.engine.senses.menu as menu

import onta.engine.static.calculator as calculator
import onta.engine.static.formulae as formulae

import onta.loader.repo as repo

import onta.util.logger as logger
import onta.util.gui as gui


STATIC_PLATES = [ 'door' ]
SWITCH_PLATES_TYPES = [ "pressure", "container", "gate" ]
MATERIAL_BLUE_900 = (20, 67, 142, 175)

log = logger.Logger('onta.view', settings.LOG_LEVEL)


# GUI Handlers

def get_app() -> QtWidgets.QApplication:
    return QtWidgets.QApplication([])    


def quit(app: QtWidgets.QApplication) -> None:
    sys.exit(app.exec_())


def get_view(
    player_device: device.Device
) -> QtWidgets.QWidget:
    view_widget, view_layout, view_frame = \
            QtWidgets.QWidget(), QtWidgets.QVBoxLayout(),  QtWidgets.QLabel()

    view_widget.resize(*player_device.dimensions)
    view_layout.addWidget(view_frame)
    view_widget.setLayout(view_layout)

    center = QtGui.QScreen.availableGeometry(
        QtWidgets.QApplication.primaryScreen()).center()
    geo = view_widget.frameGeometry()
    geo.moveCenter(center)
    view_widget.move(geo.topLeft())

    return view_widget


class Renderer():
    """_summary_
    """

    player_device = None
    """
    """
    world_frame = None
    """
    """
    static_cover_frame = munch.Munch({})
    """
    """
    static_back_frame = munch.Munch({})
    """
    """


    @staticmethod
    def render_ordered_dict(
        unordered_dict
    ) -> OrderedDict:
        # doesnt work. need to rethink this entirely.
        render_map = {}
        ordered_dict = OrderedDict()

        if len(unordered_dict)>0:
            for dict_key, dict_value in unordered_dict.items():
                render_map[dict_value['order']] = dict_key

            ordered_map = list(render_map.keys())
            ordered_map.sort()
            for order in ordered_map:
                ordered_dict[render_map[order]] = unordered_dict[render_map[order]]
        
        return ordered_dict


    def __init__(
        self, 
        game_world: world.World, 
        repository: repo.Repo, 
        player_device: device.Device
    ):
        """
        .. note:
            No references are kept to `static_world` or `repository`.
        """
        self.player_device = player_device
        self.static_cover_frame = {
            layer: gui.new_image(game_world.dimensions) 
            for layer in game_world.layers
        }
        self.static_back_frame = {
            layer: gui.new_image(game_world.dimensions)
            for layer in game_world.layers
        }

        self._render_tiles(game_world, repository)
        self._render_sets(game_world, repository)


    def _render_tiles(
        self, 
        game_world: world.World, 
        repository: repo.Repo
    ) -> None:
        log.debug('Rendering tile sets', '_render_tiles')

        for layer in game_world.layers:
            for group_key, group_conf in game_world.get_tilesets(layer).items():
                log.verbose(f'Rendering {group_key} tiles', '_render_tiles')

                group_tile = repository.get_form_frame('tiles', group_key)

                for set_conf in group_conf.sets:
                    start = calculator.scale(
                        ( set_conf.start.x, set_conf.start.y ), 
                        game_world.tile_dimensions,
                        set_conf.start.units
                    )
                    set_dim = ( set_conf.multiply.w, set_conf.multiply.h)

                    log.verbose(
                        f'Rendering at {start} with dimensions {set_dim}', 
                        '_render_tiles'
                    )
                    
                    for i in range(set_dim[0]):
                        for j in range(set_dim[1]):
                            dim = (
                                start[0] + game_world.tile_dimensions[0]*i, 
                                start[1] + game_world.tile_dimensions[1]*j
                            )

                            if set_conf.get('cover'):
                                self.static_cover_frame[layer].paste(
                                    group_tile, 
                                    dim, 
                                    group_tile
                                )
                                continue
                            
                            self.static_back_frame[layer].paste(
                                    group_tile, 
                                    dim, 
                                    group_tile
                                )


    def _render_sets(
        self, 
        game_world: world.World, 
        repository: repo.Repo
    ) -> None:
        """Renders static sets onto the static world frames. This method is only called once per session, when the game engine is initializing.

        :param game_world: _description_
        :type game_world: world.World
        :param repository: _description_
        :type repository: repo.Repo

        .. note:
            Only _Doors_ are considered static platesets. All other types of plates need to be re-rendered. Therefore, this method will only render _Door_\s.
        """
        log.debug('Rendering strut and plate sets', '_render_sets')
    
        for layer in game_world.layers:
            strutsets =  game_world.get_strutsets(layer)
            platesets = game_world.get_platesets(layer)
            strut_keys = list(strutsets.keys())
            unordered_groups = strutsets
            unordered_groups.update(platesets)

            render_map = self.render_ordered_dict(unordered_groups)
            # TODO: render map doesn't work...should be able to iterate over it instaed of 
            # unordered groups

            for group_key, group_conf in unordered_groups.items():
                if group_key in strut_keys or \
                    (game_world.plate_properties.get(group_key) and \
                        game_world.plate_properties.get(group_key).type in STATIC_PLATES):

                    group_type="strut" if group_key in strut_keys else "plate"
                    group_frame = repository.get_form_frame(group_type, group_key)
                    log.debug(f'Rendering {group_type} {group_key}s', '_render_sets')

                    for set_conf in group_conf.sets:
                        start = calculator.scale(
                            ( set_conf.start.x, set_conf.start.y ), 
                            game_world.tile_dimensions,
                            set_conf.start.units
                        )
                        log.verbose(f'Rendering at {start}', '_sets')

                        if set_conf.get('cover'):
                            self.static_cover_frame.get(layer).alpha_composite(
                                group_frame, 
                                start, 
                            )
                            continue
                        self.static_back_frame.get(layer).alpha_composite(
                            group_frame, 
                            start, 
                        )
    

    def _render_variable_platesets(
        self, 
        game_world: world.World, 
        repository: repo.Repo,
        crop: bool
    ) -> None:
        unordered_groups = game_world.get_platesets(game_world.layer)
        render_map = self.render_ordered_dict(unordered_groups)

        # and anyway, plates need rendered by type.
        #   first pressures and then everything else
        for group_key, group_conf in render_map.items():
            group_frame = repository.get_form_frame('plates', group_key)
            group_type = game_world.plate_properties.get(group_key).type


            if group_type in STATIC_PLATES:
                continue

            log.infinite(
                f'Rendering {group_type} {group_key} plates', 
                '_render_variable_platesets'
            )

            for i, set_conf in enumerate(group_conf.sets):
                start = calculator.scale(
                    ( set_conf.start.x, set_conf.start.y), 
                    game_world.tile_dimensions,
                    set_conf.start.units
                )
                if group_type not in SWITCH_PLATES_TYPES:
                    object_dim = (
                        start[0],
                        start[1],
                        group_frame.size[0],
                        group_frame.size[1]
                    )
                else:
                    object_dim = (
                        start[0],
                        start[1],
                        group_frame.on.size[0],
                        group_frame.on.size[1]
                    )
                player_dim = (
                    game_world.hero.position.x,
                    game_world.hero.position.y,
                    game_world.sprite_dimensions[0],
                    game_world.sprite_dimensions[1]
                )

                if crop and not formulae.on_screen(
                    player_dim, 
                    object_dim, 
                    self.player_device.dimensions, 
                    game_world.dimensions
                ):
                    continue 

                log.infinite(f'Rendering at {start}', '_render_variable_plates')

                if group_type not in SWITCH_PLATES_TYPES:
                    self.world_frame.alpha_composite(group_frame, start)
                    continue

                if game_world.switch_map.get(game_world.layer).get(group_key).get(str(i)):
                    self.world_frame.alpha_composite(group_frame.on, start)
                    continue
                self.world_frame.alpha_composite(group_frame.off, start)


    def _render_static(
        self, 
        layer_key: str, 
        cover: bool = False
    ):
        if cover:
            return self.world_frame.alpha_composite(
                self.static_cover_frame.get(layer_key), 
                ( 0,0 ),
            )
        return self.world_frame.alpha_composite(
                self.static_back_frame.get(layer_key), 
                ( 0, 0 ),
            )


    def _render_sprites(
        self,
        game_world: world.World, 
        repository: repo.Repo,
        crop: bool
    ) -> None:
        """_summary_

        :param game_world: _description_
        :type game_world: world.World
        :param repository: _description_
        :type repository: repo.Repo

        .. note::
            Base frame gets rendered no matter what, while accent frames only get rendered if sprite does not have armor equipped. If armor is equipped, armor frames are rendered in place.
        .. note::
            Equipment frame only gets rendered if it is binded to a sprite state in the apparel configuration file. 
        """
        sprites = game_world.get_sprites(game_world.layer)
        for sprite_key, sprite in sprites.items():
            sprite_position = gui.int_tuple(( sprite.position.x, sprite.position.y ))

            sprite_stature_key = formulae.compose_animate_stature(
                sprite,
                game_world.sprite_stature
            )
            # BASE RENDERING
            sprite_base_frame, sprite_accent_frame = repository.get_sprite_frame(
                sprite_key, 
                sprite_stature_key, 
                sprite.frame
            )

            sprite_dim = (
                sprite_position[0],
                sprite_position[1],
                sprite_base_frame.size[0],
                sprite_base_frame.size[1]
            )
            player_dim = (
                game_world.hero.position.x,
                game_world.hero.position.y,
                game_world.sprite_dimensions[0],
                game_world.sprite_dimensions[1]
            )

            if crop and not formulae.on_screen(
                player_dim,
                sprite_dim,
                self.player_device.dimensions,
                game_world.dimensions,
            ):
                continue

            self.world_frame.alpha_composite(sprite_base_frame, sprite_position)

            # ARMOR RENDERING
            if sprite.armor:
                animate_statures = \
                    game_world.apparel_stature.armor.get(sprite.armor).animate_statures

                if (isinstance(animate_statures, str) and animate_statures == 'all') or \
                    (isinstance(animate_statures, list) and sprite_stature_key in animate_statures):

                    armor_frame = repository.get_apparel_frame(
                        'armor',
                        sprite.armor,
                        sprite_stature_key,
                        sprite.frame
                    )
                    self.world_frame.alpha_composite(armor_frame, sprite_position)

            elif sprite_accent_frame:
                self.world_frame.alpha_composite(sprite_accent_frame, sprite_position)

            # EQUIPMENT RENDERING
            if any(slot for slot in sprite.slots.values()):
                enabled = [ slot for slot in sprite.slots.values() if slot ]

                for enabled_equipment in enabled:
                    animate_statures = \
                        game_world.apparel_stature.equipment.get(enabled_equipment).animate_statures


                    if (isinstance(animate_statures, str) and animate_statures == 'all') or \
                        (isinstance(animate_statures, list) and sprite_stature_key in animate_statures):

                        equipment_frame = repository.get_apparel_frame(
                            'equipment',
                            enabled_equipment,
                            sprite_stature_key,
                            sprite.frame
                        )
                        self.world_frame.alpha_composite(equipment_frame, sprite_position)



    def _render_slots(
        self, 
        headsup_display: hud.HUD, 
        repository: repo.Repo
    ) -> None:
        rendering_points = headsup_display.get_rendering_points('slot')

        cap_dir = headsup_display.get_cap_directions()
        buffer_dir = headsup_display.get_buffer_direction()

        # slot names
        render_order = iter(headsup_display.properties.slots.maps)

        cap_frames = repository.get_slot_frames(headsup_display.media_size, 'cap')
        buffer_frames = repository.get_slot_frames(headsup_display.media_size, 'buffer'
        )
        # TODO: I don't like the view creating the data structure here...
        # this should be done in repo...
        slot_frames = munch.Munch({
            'enabled': repository.get_slot_frames(headsup_display.media_size, 'enabled'),
            'disabled':  repository.get_slot_frames(headsup_display.media_size, 'disabled'),
            'active': repository.get_slot_frames(headsup_display.media_size, 'active')
        })

        # cap, then alternate buffer and slot until last cap
        for i, render_point in enumerate(rendering_points):
            if i == 0:
                render_frame = cap_frames.get(cap_dir[0])
            elif i == len(rendering_points) -1:
                render_frame = cap_frames.get(cap_dir[1])
            elif i % 2 == 0:
                render_frame = buffer_frames.get(buffer_dir)
            else:
                render_key = next(render_order)
                # map from slot name -> slot state -> slot frame
                render_frame = slot_frames.get(
                    headsup_display.get_frame_map('slot').get(render_key)
                )

            self.world_frame.alpha_composite(
                render_frame, 
                gui.int_tuple(render_point)
            )

    
    def _render_mirrors(
        self, 
        headsup_display: hud.HUD, 
        repository: repo.Repo
    ) -> None:

        rendering_points = headsup_display.get_rendering_points('life')

        for i, frame_key in headsup_display.get_frame_map('life').items():
            life_frame = repository.get_mirror_frame(
                headsup_display.media_size, 
                'life', 
                frame_key
            )
            render_point = rendering_points[i]
            self.world_frame.alpha_composite(life_frame, gui.int_tuple(render_point),)


    def _render_packs(
        self, 
        headsup_display: hud.HUD, 
        repository: repo.Repo
    ) -> None:

        # avatar rendering points include slot avatars and wallet avatars...
        for pack_key in hud.PACK_TYPES:
            pack_map = headsup_display.get_frame_map(pack_key)
            pack_rendering_points = headsup_display.get_rendering_points(pack_key)

            for i, render_point in enumerate(pack_rendering_points):
                # offset by slots
                pack_frame = repository.get_pack_frame(
                    headsup_display.media_size,
                    pack_key,
                    pack_map[i]
                )
                self.world_frame.alpha_composite(
                    pack_frame, 
                    gui.int_tuple(render_point)
                )


    def _render_avatars(
        self,
        headsup_display: hud.HUD,
        repository: repo.Repo
    ) -> None:

        avatar_rendering_points = headsup_display.get_rendering_points('avatar')
        avatar_frame_map = headsup_display.get_frame_map('avatar')
        avatar_set_map = munch.Munch({
            'equipment': 4, # slots 
            'inventory': 8 # slots + wallets + belt + bag
        })

        for i, render_point in enumerate(avatar_rendering_points):
            if not render_point or not avatar_frame_map[str(i)]:
                continue

            if i < avatar_set_map.equipment and \
                i < avatar_set_map.inventory:
                set_key = 'equipment'
            elif i >= avatar_set_map.equipment and \
                i < avatar_set_map.inventory:
                set_key = 'inventory'
            else: 
                set_key = None

            if not set_key:
                continue

            avatar_frame = repository.get_avatar_frame(
                set_key,
                avatar_frame_map[str(i)]
            )
            self.world_frame.alpha_composite(
                avatar_frame,
                gui.int_tuple(render_point),
            )


    def _render_menu(
        self, 
        menu: menu.Menu, 
        repository: repo.Repo
    ) -> None:
        # TODO: alpha and overlay should be part of configuration or styles
        gui.replace_alpha(self.world_frame, 127)
        overlay = gui.channels(self.player_device.dimensions, MATERIAL_BLUE_900)

        self.world_frame.paste(overlay, ( 0,0 ), overlay)

        btn_rendering_points = menu.get_rendering_points('button')
        
        btn_frame_map, btn_piece_map = menu.button_maps()

        for i, render_point in enumerate(btn_rendering_points):
            render_frame = repository.get_menu_frame(
                menu.media_size, 
                btn_frame_map[i],
                btn_piece_map[i]
            )
            self.world_frame.alpha_composite(
                render_frame,
                gui.int_tuple(render_point),
            )


    def render(
        self, 
        game_world: world.World, 
        repository: repo.Repo, 
        headsup_display: hud.HUD, 
        menu: menu.Menu,
        crop: bool = True, 
        layer: str = None
    ) -> Image.Image:
        """_summary_

        :param game_world: _description_
        :type game_world: world.World
        :param repository: _description_
        :type repository: repo.Repo
        :param crop: _description_, defaults to True
        :type crop: bool, optional
        :param layer: _description_, defaults to None
        :type layer: str, optional
        :return: _description_
        :rtype: _type_
        """
        self.world_frame = gui.new_image(game_world.dimensions)

        if layer is not None:
            layer_buffer = game_world.layer
            game_world.layer = layer

        self._render_static(game_world.layer, False)
        self._render_variable_platesets(game_world, repository, crop)
        self._render_sprites(game_world, repository, crop)
        self._render_static(game_world.layer, True)

        if layer is not None:
            game_world.layer = layer_buffer
            
        if crop:
            world_dim = game_world.dimensions
            hero_pt = ( 
                game_world.hero.position.x, 
                game_world.hero.position.y
            )
            crop_box = formulae.screen_crop_box(
                self.player_device.dimensions, 
                world_dim, 
                hero_pt
            )
            self.world_frame = self.world_frame.crop(crop_box)
        
        if menu.menu_activated:
            self._render_menu(menu, repository)

        if headsup_display.hud_activated:
            self._render_slots(headsup_display, repository)
            self._render_mirrors(headsup_display, repository)
            self._render_packs(headsup_display, repository)
            self._render_avatars(headsup_display, repository)

        return self.world_frame

    # Rendering connection to GUI
    def view(
        self, 
        game_world: world.World, 
        view_widget: QtWidgets.QWidget, 
        headsup_display: hud.HUD,
        menu: menu.Menu,
        repository: repo.Repo
    ) -> QtWidgets.QWidget: 
        """_summary_

        :param game_world: _description_
        :type game_world: world.World
        :param view_widget: _description_
        :type view_widget: QtWidgets.QWidget
        :param headsup_display: _description_
        :type headsup_display: interface.HUD
        :param menu: _description_
        :type menu: interface.Menu
        :param repository: _description_
        :type repository: repo.Repo
        :return: _description_
        :rtype: QtWidgets.QWidget
        """
        cropped = self.render(
            game_world, 
            repository, 
            headsup_display, 
            menu
        )

        pix = gui.convert_to_gui(cropped)

        view_frame = view_widget.layout().itemAt(0).widget() 
        view_frame.setPixmap(pix)
        return view_widget