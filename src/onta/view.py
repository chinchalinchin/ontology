import sys
from collections import OrderedDict

from PySide6 import QtWidgets, QtGui

import onta.device as device
import onta.settings as settings
import onta.world as world
import onta.interface as interface
import onta.engine.calculator as calculator
import onta.load.repo as repo
import onta.util.logger as logger
import onta.util.gui as gui


SWITCH_PLATES = ['container', 'pressure', 'gate']
MATERIAL_BLUE_900 = (20, 67, 142, 175)

log = logger.Logger('onta.view', settings.LOG_LEVEL)


def get_app() -> QtWidgets.QApplication:
    return QtWidgets.QApplication([])    


def quit(app) -> None:
    sys.exit(app.exec_())


def get_view(player_device: device.Device) -> QtWidgets.QWidget:
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
    static_cover_frame = None
    """
    """
    static_back_frame = None
    """
    """
    world_frame = None
    """
    """


    @staticmethod
    def calculate_crop_box(screen_dim: tuple, world_dim: tuple, hero_pt: tuple):
        left_breakpoint = screen_dim[0]/2
        right_breakpoint = world_dim[0] - screen_dim[0]/2
        top_breakpoint = screen_dim[1]/2
        bottom_breakpoint = world_dim[1] - screen_dim[1]/2

        if hero_pt[0] >= 0 and hero_pt[0] <= left_breakpoint:
            crop_x = 0
        elif hero_pt[0] > right_breakpoint:
            crop_x = world_dim[0] - screen_dim[0]
        else:
            crop_x = hero_pt[0] - screen_dim[0]/2

        if hero_pt[1] >= 0 and hero_pt[1] <= top_breakpoint:
            crop_y = 0
        elif hero_pt[1] > bottom_breakpoint:
            crop_y = world_dim[1] - screen_dim[1]
        else:
            crop_y = hero_pt[1] - screen_dim[1]/2

        crop_width = crop_x + screen_dim[0]
        crop_height = crop_y + screen_dim[1]
        return (crop_x, crop_y, crop_width, crop_height)


    @staticmethod
    def render_ordered_dict(unordered_dict):
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


    def _render_tiles(self, game_world: world.World, repository: repo.Repo) -> None:
        log.debug('Rendering tile sets', 'Repo._render_tiles')

        for layer in game_world.layers:
            for group_key, group_conf in game_world.get_tilesets(layer).items():
                log.debug(f'Rendering {group_key} tiles', 'Repo._render_tiles')

                group_tile = repository.get_form_frame('tiles', group_key)
                for set_conf in group_conf['sets']:
                    start = calculator.scale(
                        (set_conf['start']['x'], set_conf['start']['y']), 
                        game_world.tile_dimensions,
                        set_conf['start']['units']
                    )
                    set_dim = (set_conf['multiply']['w'], set_conf['multiply']['h'])

                    log.debug(f'Rendering group set at {start[0], start[1]} with dimensions {set_dim[0], set_dim[1]}', 'Repo._render_tiles')
                    
                    for i in range(set_dim[0]):
                        for j in range(set_dim[1]):
                            dim = (start[0] + game_world.tile_dimensions[0]*i, 
                                start[1] + game_world.tile_dimensions[1]*j)

                            if set_conf.get('cover'):
                                self.static_cover_frame[layer].paste(group_tile, dim, group_tile)
                            else:
                                self.static_back_frame[layer].paste(group_tile, dim, group_tile)


    def _render_sets(self, game_world: world.World, repository: repo.Repo):
        """Renders static sets onto the static world frames. This method is only called once per session, when the game engine is initializing.

        :param game_world: _description_
        :type game_world: world.World
        :param repository: _description_
        :type repository: repo.Repo

        .. note:
            Only _Doors_ are considered static platesets. All other types of plates need to be re-rendered. Therefore, this method will only render _Door_\s.
        """
        log.debug('Rendering strut and plate sets', 'Repo._render_static_sets')
    
        for layer in game_world.layers:
            strutsets, platesets =  game_world.get_strutsets(layer), game_world.get_platesets(layer)
            strut_keys = list(strutsets.keys())

            unordered_groups = strutsets
            unordered_groups.update(platesets)

            render_map = self.render_ordered_dict(unordered_groups)
            # TODO: render map doesn't work...should be able to iterate over it instaed of 
            # unordered groups

            for group_key, group_conf in unordered_groups.items():
                if group_key in strut_keys or \
                    (game_world.plate_property_conf.get(group_key) and \
                        game_world.plate_property_conf.get('type') == 'door'):

                    log.debug(f'Rendering {group_key} struts', 'Repo._render_static_sets')

                    if group_key in strut_keys:
                        group_frame = repository.get_form_frame('struts', group_key)
                    else:
                        group_frame = repository.get_form_frame('plates', group_key)

                    for set_conf in group_conf['sets']:
                        start = calculator.scale(
                            (set_conf['start']['x'], set_conf['start']['y']), 
                            game_world.tile_dimensions,
                            set_conf['start']['units']
                        )
                        log.debug(f'Rendering group set at {start[0], start[1]}', 'Repo._render_static_sets')

                        if set_conf.get('cover'):
                            self.static_cover_frame[layer].paste(group_frame, start, group_frame)
                        else:
                            self.static_back_frame[layer].paste(group_frame, start, group_frame)
    

    def _render_typed_platesets(self, game_world: world.World, repository: repo.Repo):
        unordered_groups = game_world.get_platesets(game_world.layer)
        render_map = self.render_ordered_dict(unordered_groups)

        for group_key, group_conf in render_map.items():
            group_frame = repository.get_form_frame('plates', group_key)
            for i, set_conf in enumerate(group_conf['sets']):
                start = calculator.scale(
                    (set_conf['start']['x'], set_conf['start']['y']), 
                    game_world.tile_dimensions,
                    set_conf['start']['units']
                )
                log.infinite(f'Rendering "{game_world.plate_property_conf[group_key]["type"]}" plate set at {start[0], start[1]}', 
                'Repo._render_typed_plates')

                if game_world.plate_property_conf[group_key]['type'] not in SWITCH_PLATES:
                    self.world_frame.paste(group_frame, start, group_frame)

                else:
                    if game_world.switch_map[game_world.layer][group_key][i]:
                        self.world_frame.paste(group_frame['on'], start, group_frame['on'])
                    else: 
                        self.world_frame.paste(group_frame['off'], start, group_frame['off'] )


    def _render_static(self, layer, cover: bool = False):
        if cover:
            self.world_frame.paste(self.static_cover_frame[layer], (0,0), self.static_cover_frame[layer])
        else:
            self.world_frame.paste(self.static_back_frame[layer], (0,0), self.static_back_frame[layer])


    def _render_spriteset(self, spriteset_key: str, game_world: world.World, repository: repo.Repo):
        spriteset = game_world.get_spriteset(spriteset_key)
        for sprite_key, sprite in spriteset.items():
            sprite_position = (int(sprite['position']['x']), int(sprite['position']['y']))
            sprite_state, sprite_frame = sprite['state'], sprite['frame']
            sprite_frame = repository.get_sprite_frame(sprite_key, sprite_state, sprite_frame)
            self.world_frame.paste(sprite_frame, sprite_position, sprite_frame)


    def _render_slots(self, headsup_display: interface.HUD, repository: repo.Repo):
        rendering_points = headsup_display.get_rendering_points('slot')

        cap_dir = headsup_display.get_cap_directions()
        buffer_dir = headsup_display.get_buffer_direction()

        render_order = iter(interface.SLOT_STATES)
        render_map = headsup_display.slot_frame_map()

        cap_frames = repository.get_slot_frames(headsup_display.media_size, 'cap')
        buffer_frames = repository.get_slot_frames(headsup_display.media_size, 'buffer')
        slot_frames = {
            'enabled': repository.get_slot_frames(headsup_display.media_size, 'enabled'),
            'disabled':  repository.get_slot_frames(headsup_display.media_size, 'disabled'),
            'active': repository.get_slot_frames(headsup_display.media_size, 'active')
        }

        for i, render_point in enumerate(rendering_points):
            if i == 0:
                render_frame = cap_frames[cap_dir[0]]
            elif i == len(rendering_points) -1:
                render_frame = cap_frames[cap_dir[1]]
            elif i % 2 == 0:
                render_frame = buffer_frames[buffer_dir]
            else:
                render_key = next(render_order)
                render_frame = slot_frames[render_map[render_key]]

            print(render_point)

            self.world_frame.paste(
                render_frame, 
                (int(render_point[0]), int(render_point[1])), 
                render_frame
            )


    def _render_mirrors(self, headsup_display: interface.HUD, repository: repo.Repo):
        rendering_points = headsup_display.get_rendering_points('mirror')
        life_map = headsup_display.life_frame_map()

        for i, fill in life_map.items():
            life_frame = repository.get_mirror_frame(
                headsup_display.media_size, 
                'life', 
                fill
            )
            render_point = rendering_points[i]
            self.world_frame.paste(
                life_frame,
                (int(render_point[0]), int(render_point[1])),
                life_frame
            )


    def _render_packs(self, headsup_display: interface.HUD, repository: repo.Repo):
        pack_map = headsup_display.pack_frame_map()

        bag_rendering_points = headsup_display.get_rendering_points('pack')

        for i, render_point in enumerate(bag_rendering_points):
            bag_frame = repository.get_pack_frame(
                headsup_display.media_size,
                'bag',
                pack_map[i]
            )
            self.world_frame.paste(
                bag_frame,
                (int(render_point[0]), int(render_point[1])),
                bag_frame
            )


    def _render_menu(self, menu: interface.Menu, repository: repo.Repo):
        gui.replace_alpha(self.world_frame, 127)
        overlay = gui.channels(
            self.player_device.dimensions, 
            MATERIAL_BLUE_900
        )
        self.world_frame.paste(
            overlay,
            (0,0),
            overlay
        )

        btn_rendering_points = menu.get_rendering_points('button')
        
        btn_frame_map, btn_piece_map = menu.button_maps()

        for i, render_point in enumerate(btn_rendering_points):
            render_frame = repository.get_menu_frame(
                menu.media_size, 
                btn_frame_map[i],
                btn_piece_map[i]
            )
            self.world_frame.paste(
                render_frame,
                (int(render_point[0]), int(render_point[1])),
                render_frame
            )


    def render(
        self, 
        game_world: world.World, 
        repository: repo.Repo, 
        headsup_display: interface.HUD, 
        menu: interface.Menu,
        crop: bool = True, 
        layer: str = None):
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
        self._render_typed_platesets(game_world, repository)
        for spriteset in ['npcs', 'villains', 'hero']:
            self._render_spriteset(spriteset, game_world, repository)
        self._render_static(game_world.layer, True)

        if layer is not None:
            game_world.layer = layer_buffer
            
        if crop:
            world_dim = game_world.dimensions
            hero_pt = (game_world.hero['position']['x'], game_world.hero['position']['y'])
            crop_box = self.calculate_crop_box(self.player_device.dimensions, world_dim, hero_pt)
            self.world_frame = self.world_frame.crop(crop_box)
        
        if menu.menu_activated:
            self._render_menu(menu, repository)

        if headsup_display.hud_activated:
            self._render_slots(headsup_display, repository)
            self._render_mirrors(headsup_display, repository)
            self._render_packs(headsup_display, repository)

        return self.world_frame


    def view(
        self, 
        game_world: world.World, 
        view_widget: QtWidgets.QWidget, 
        headsup_display: interface.HUD,
        menu: interface.Menu,
        repository: repo.Repo
    ):        
        cropped = self.render(game_world, repository, headsup_display, menu)

        pix = gui.convert_to_gui(cropped)

        view_frame = view_widget.layout().itemAt(0).widget() 
        view_frame.setPixmap(pix)
        return view_widget