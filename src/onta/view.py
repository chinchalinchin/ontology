import sys
from collections import OrderedDict

from PySide6 import QtWidgets, QtGui
from PIL.ImageQt import ImageQt

import onta.device as device
import onta.settings as settings
import onta.world as world
import onta.hud as hud
import onta.engine.calculator as calculator
import onta.load.repo as repo
import onta.util.logger as logger
import onta.util.gui as gui


SWITCH_PLATES = ['container', 'pressure', 'gate']

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
    slot_frames = None
    cap_frames = None


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
        render_map = {}
        ordered_dict = OrderedDict()

        if len(unordered_dict)>0:
            for dict_key, dict_value in unordered_dict.items():
                render_order = dict_value['order']
                render_map[render_order] = dict_key

            ordered_map = list(render_map.keys())
            ordered_map.sort()
            for order in ordered_map:
                ordered_dict[render_map[order]] = unordered_dict[render_map[order]]
        
        return ordered_dict


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
            return (0, 180)
        return (180, 0)
        

    def __init__(
        self, 
        game_world: world.World, 
        repository: repo.Repo, 
        headsup_display: hud.HUD, 
        player_device: device.Device
    ):
        """
        .. notes:
            - No references are kept to `static_world` or `repository`.
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
        self._init_interface_set(repository, headsup_display)
        self._render_tiles(game_world, repository)
        self._render_sets(game_world, repository)


    def _init_interface_set(self, repository: repo.Repo, headsup_display: hud.HUD):
        slot_props = headsup_display.hud_conf[headsup_display.media_size]['slots']


        cap_frame = repository.get_interface_frame(
            'slot', 
            headsup_display.media_size,
            'cap'
        )
        (up_adjust, left_adjust, right_adjust, down_adjust) = \
            self.adjust_cap_rotation(
                slot_props['cap']['image']['definition']
            )
        self.cap_frames = {
            'up': cap_frame.rotate(up_adjust),
            'left': cap_frame.rotate(left_adjust),
            'down': cap_frame.rotate(down_adjust),
            'right': cap_frame.rotate(right_adjust)
        }


        buffer_frame = repository.get_interface_frame(
            'slot', 
            headsup_display.media_size,
            'buffer'
        )
        (vertical_adjust, horizontal_adjust) = \
            self.adjust_buffer_rotation(
              slot_props['buffer']['image']['definition']  
            )
        self.buffer_frames = {
            'vertical': buffer_frame.rotate(vertical_adjust),
            'horizontal': buffer_frame.rotate(horizontal_adjust)
        }


        self.slot_frames = {
            'empty': repository.get_interface_frame(
                'slot', 
                headsup_display.media_size,
                'empty'
            ),
            'equipped': repository.get_interface_frame(
                'slot',
                headsup_display.media_size,
                'equipped'
            )
        }


    def _render_tiles(self, game_world: world.World, repository: repo.Repo) -> None:
        log.debug('Rendering tile sets', 'Repo._render_tiles')

        for layer in game_world.layers:
            for group_key, group_conf in game_world.get_tilesets(layer).items():
                log.debug(f'Rendering {group_key} tiles', 'Repo._render_tiles')

                group_tile = repository.get_asset_frame('tiles', group_key)
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

        .. notes:
            - Only _Doors_ are considered static platesets. All other types of plates need to be re-rendered.
        """
        log.debug('Rendering strut and plate sets', 'Repo._render_static_sets')

        for static_set in ['struts', 'plates']:
            for layer in game_world.layers:
                if static_set == 'struts':
                    unordered_groups = game_world.get_strutsets(layer)
                elif static_set == 'plates':
                    unordered_groups = game_world.get_platesets(layer)

                render_map = self.render_ordered_dict(unordered_groups)

                for group_key, group_conf in render_map.items():
                    if static_set == 'struts' or \
                        (static_set == 'plates' and \
                            game_world.plate_property_conf[group_key]['type'] == 'door'):

                        log.debug(f'Rendering {group_key} struts', 'Repo._render_static_sets')

                        group_frame = repository.get_asset_frame(static_set, group_key)
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

        # This definitely isn't rendering in the intended order...

        for group_key, group_conf in render_map.items():
            group_frame = repository.get_asset_frame('plates', group_key)
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


    def _render_slots(self, headsup_display: hud.HUD, repository: repo.Repo):
        slot_styles = headsup_display.styles[headsup_display.media_size]['slots']
        
        cap_dirs = headsup_display.get_cap_directions()
        buffer_dir = headsup_display.get_buffer_direction()
        

        # horizontal
        # 1 = start, 2 = 1 + cap_width, 3 = 2 + slot_width, 4 = 3 + buffer_width, 5 = 4 + slot_width
        startcap_frame, endcap_frame = self.cap_frames[cap_dirs[0]], self.cap_frames[cap_dirs[1]]
        buffer_frame = self.buffer_frames[buffer_dir]

        i = 0
        for slot_key, slot_frame_key in headsup_display.slot_frame_map().items():
            # TODO: will need slot_key for avatars...

            slot_frame = self.slot_frames[slot_frame_key]
            i += 1

    def render(self, game_world: world.World, repository: repo.Repo, headsup_display: hud.HUD, crop: bool = True, layer: str = None):
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
        
        if headsup_display.activated:
            self._render_slots(headsup_display, repository)

        return self.world_frame

    def view(self, game_world: world.World, view_widget: QtWidgets.QWidget, headsup_display: hud.HUD,repository: repo.Repo):

        # TODO: render HUD
        
        cropped = self.render(game_world, repository, headsup_display)

        qim = ImageQt(cropped)
        pix = QtGui.QPixmap.fromImage(qim)

        view_frame = view_widget.layout().itemAt(0).widget() 
        view_frame.setPixmap(pix)
        return view_widget