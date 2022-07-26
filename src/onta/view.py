import sys


from collections import OrderedDict

from PySide6 import QtWidgets, QtGui
from PIL.ImageQt import ImageQt

import onta.settings as settings
import onta.world as world
import onta.engine.calculator as calculator
import onta.load.repo as repo
import onta.util.logger as logger
import onta.util.gui as gui


log = logger.Logger('onta.view', settings.LOG_LEVEL)

SWITCH_PLATES = ['container', 'pressure', 'gate']

def get_app() -> QtWidgets.QApplication:
    return QtWidgets.QApplication([])    

def quit(app) -> None:
    sys.exit(app.exec_())

def get_view() -> QtWidgets.QWidget:
    view_widget, view_layout, view_frame = \
            QtWidgets.QWidget(), QtWidgets.QVBoxLayout(),  QtWidgets.QLabel()

    view_widget.resize(settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
    view_layout.addWidget(view_frame)
    view_widget.setLayout(view_layout)

    center = QtGui.QScreen.availableGeometry(
        QtWidgets.QApplication.primaryScreen()).center()
    geo = view_widget.frameGeometry()
    geo.moveCenter(center)
    view_widget.move(geo.topLeft())

    return view_widget

class Renderer():
    
    static_cover_frame = None
    static_back_frame = None
    world_frame = None

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

    def __init__(self, static_world: world.World, repository: repo.Repo):
        """
        .. notes:
            - No references are kept to `static_world` or `repository`.
        """
        self.static_cover_frame = {}
        self.static_back_frame = {}
        for layer in static_world.layers:
            self.static_back_frame[layer] = gui.new_image(static_world.dimensions)
            self.static_cover_frame[layer] = gui.new_image(static_world.dimensions)
        self._render_tiles(static_world, repository)
        self._render_static_sets(static_world, repository)

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

    def _render_static_sets(self, game_world: world.World, repository: repo.Repo):
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
    
    def _render_typed_plates(self, game_world: world.World, repository: repo.Repo, plate_type: str):
        unordered_groups = game_world.get_platesets(game_world.layer)
        render_map = self.render_ordered_dict(unordered_groups)

        for group_key, group_conf in render_map.items():
            if game_world.plate_property_conf[group_key]['type'] == plate_type:
                group_frame = repository.get_asset_frame('plates', group_key)
                for i, set_conf in enumerate(group_conf['sets']):
                    start = calculator.scale(
                        (set_conf['start']['x'], set_conf['start']['y']), 
                        game_world.tile_dimensions,
                        set_conf['start']['units']
                    )
                    log.infinite(f'Rendering "{plate_type}" plate set at {start[0], start[1]}', 
                    'Repo._render_typed_plates')

                    if plate_type not in SWITCH_PLATES:
                        self.world_frame.paste(group_frame, start, group_frame)

                    else:
                        if game_world.switch_map[game_world.layer][group_key][i]:
                            self.world_frame.paste(group_frame['on'], start, group_frame['on'])
                        else: 
                            self.world_frame.paste(group_frame['off'], start, group_frame['off'] )

    def _render_switch_plates(self, game_world: world.World, repository: repo.Repo):
        pass


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

    def render(self, game_world: world.World, repository: repo.Repo, crop: bool = True, layer: str = None):
        self.world_frame = gui.new_image(game_world.dimensions)

        if layer is not None:
            layer_buffer = game_world.layer
            game_world.layer = layer

        self._render_static(game_world.layer, False)
        for typed_plate in ['mass', 'container', 'gate', 'pressure']:
            self._render_typed_plates(game_world, repository, typed_plate)
        for spriteset in ['npcs', 'villains', 'hero']:
            self._render_spriteset(spriteset, game_world, repository)
        self._render_static(game_world.layer, True)

        if layer is not None:
            game_world.layer = layer_buffer
            
        if crop:
            screen_dim = (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
            world_dim = game_world.dimensions
            hero_pt = (game_world.hero['position']['x'], game_world.hero['position']['y'])
            crop_box = self.calculate_crop_box(screen_dim, world_dim, hero_pt)

            self.world_frame = self.world_frame.crop(crop_box)

        return self.world_frame

    def view(self, game_world: world.World, view_widget: QtWidgets.QWidget, repository: repo.Repo):
        cropped = self.render(game_world, repository)
        qim = ImageQt(cropped)
        pix = QtGui.QPixmap.fromImage(qim)

        view_frame = view_widget.layout().itemAt(0).widget() 
        view_frame.setPixmap(pix)
        return view_widget