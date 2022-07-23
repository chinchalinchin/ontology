import sys

from PySide6 import QtWidgets, QtGui
from PIL.ImageQt import ImageQt

import onta.settings as settings
import onta.world as world
import onta.load.repo as repo
import onta.util.logger as logger
import onta.util.gui as gui


log = logger.Logger('onta.view', settings.LOG_LEVEL)

def init() -> QtWidgets.QApplication:
    return QtWidgets.QApplication([])    

def quit(app) -> None:
    sys.exit(app.exec_())

def view() -> QtWidgets.QWidget:
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
    hero_frame = None

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
    def generate_render_order(set):
        pass

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
        self._render_struts(static_world, repository)

    def _render_tiles(self, game_world: world.World, repository: repo.Repo) -> None:
        log.debug('Rendering tile sets', 'Repo._render_tiles')

        for layer in game_world.layers:
            for group_key, group_conf in game_world.get_tilesets(layer).items():
                group_tile = repository.get_layer('tiles', group_key)

                log.debug(f'Rendering {group_key} tiles', 'Repo._render_tiles')

                for set_conf in group_conf['sets']:
                    if set_conf['start']['tile_units'] == 'default':
                        start = (set_conf['start']['x']*settings.TILE_DIM[0], 
                            set_conf['start']['y']*settings.TILE_DIM[1])

                    elif set_conf['start']['tile_units'] == 'relative':
                        start = (set_conf['start']['x']*group_tile.size[0], 
                            set_conf['start']['y']*group_tile.size[1])
                    else:
                        start = (set_conf['start']['x'], set_conf['start']['y'])

                    set_dim = (set_conf['dim']['w'], set_conf['dim']['h'])

                    log.debug(f'Rendering group set at {start[0], start[1]} with dimensions {set_dim[0], set_dim[1]}', 'Repo._render_tiles')
                    
                    for i in range(set_dim[0]):
                        for j in range(set_dim[1]):
                            # TODO: see above
                            dim = (start[0] + settings.TILE_DIM[0]*i, 
                                start[1] + settings.TILE_DIM[1]*j)

                            if set_conf['cover']:
                                self.static_cover_frame[layer].paste(group_tile, dim, group_tile)
                            else:
                                self.static_back_frame[layer].paste(group_tile, dim, group_tile)

    def _render_struts(self, game_world: world.World, repository: repo.Repo):
        log.debug('Rendering strut sets', 'Repo._render_tiles')

        for layer in game_world.layers:
            for strut_type in [True, False]:
                # TODO: need to order strutsets by rendering order
                for group_key, group_conf in game_world.get_strutsets(layer, strut_type).items():
                    group_strut = repository.get_layer('struts', group_key)
                    group_sets = group_conf['sets']

                    log.debug(f'Rendering {group_key} struts', 'Repo._render_struts')

                    for set_conf in group_sets:
                        if set_conf['start']['tile_units'] == 'default':
                            start = (set_conf['start']['x']*settings.TILE_DIM[0], 
                                set_conf['start']['y']*settings.TILE_DIM[1])

                        elif set_conf['start']['tile_units'] == 'relative':
                            start = (set_conf['start']['x']*group_strut.size[0], 
                                set_conf['start']['y']*group_strut.size[1])

                        else:
                            start = (set_conf['start']['x'], set_conf['start']['y'])

                        log.debug(f'Rendering group set at {start[0], start[1]}', 'Repo._render_struts')

                        if set_conf['cover']:
                            self.static_cover_frame[layer].paste(group_strut, start, group_strut)
                        else:
                            self.static_back_frame[layer].paste(group_strut, start, group_strut)
                    if strut_type:
                        print(group_sets)
    
    def _render_static(self, layer, cover: bool = False):
        if cover:
            self.world_frame.paste(self.static_cover_frame[layer], (0,0), self.static_cover_frame[layer])
        else:
            self.world_frame.paste(self.static_back_frame[layer], (0,0), self.static_back_frame[layer])

    def _render_spriteset(self, spriteset: str, game_world: world.World, repository: repo.Repo):
        # TODO: conditionally render based on layer
        if spriteset == 'hero':
            iter_set = { 'hero': game_world.hero }
        elif spriteset == 'npcs':
            iter_set = game_world.npcs
        elif spriteset == 'villains':
            iter_set = game_world.villains

        for sprite_key, sprite in iter_set.items():
            sprite_position = (int(sprite['position']['x']), int(sprite['position']['y']))
            sprite_state, sprite_frame = sprite['state'], sprite['frame']
            sprite_frame = repository.get_sprite(sprite_key, sprite_state, sprite_frame)
            self.world_frame.paste(sprite_frame, sprite_position, sprite_frame)

    def render(self, game_world: world.World, view_widget: QtWidgets.QWidget, repository: repo.Repo):
        view_frame = view_widget.layout().itemAt(0).widget() 
        self.world_frame = gui.new_image(game_world.dimensions)

        self._render_static(game_world.layer, False)
        for spriteset in ['npcs', 'villains', 'hero']:
            self._render_spriteset(spriteset, game_world, repository)
        self._render_static(game_world.layer, True)

        screen_dim = (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
        world_dim = game_world.dimensions
        hero_pt = (game_world.hero['position']['x'], game_world.hero['position']['y'])
        crop_box = self.calculate_crop_box(screen_dim, world_dim, hero_pt)

        qim = ImageQt(self.world_frame.crop(crop_box))
        pix = QtGui.QPixmap.fromImage(qim)
        view_frame.setPixmap(pix)
        return view_widget