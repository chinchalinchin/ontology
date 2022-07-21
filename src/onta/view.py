import sys

from PySide6 import QtWidgets, QtGui
from PIL.ImageQt import ImageQt

import onta.settings as settings
import onta.world as world
import onta.load.repo as repo
import onta.util.logger as logger
import onta.util.gui as gui


log = logger.Logger('ontology.onta.view', settings.LOG_LEVEL)

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
    static_frame = None
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

    def __init__(self, static_world, repository):
        # NOTE: no references are kept to static_world or repository;
        # they pass through and return to main.py
        self._render_tiles(static_world, repository)
        self._render_struts(static_world, repository)

    def render(self, game_world: world.World, view_widget: QtWidgets.QWidget, repo: repo.Repo):
        view_frame = view_widget.layout().itemAt(0).widget() 
   
        self._render_static(game_world)
        self._render_hero(game_world, repo)

        screen_dim = (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
        world_dim = game_world.dimensions
        hero_pt = (game_world.hero['position']['x'], game_world.hero['position']['y'])
        crop_box = self.calculate_crop_box(screen_dim, world_dim, hero_pt)

        qim = ImageQt(self.world_frame.crop(crop_box))
        pix = QtGui.QPixmap.fromImage(qim)
        view_frame.setPixmap(pix)
        return view_widget


    def _render_tiles(self, game_world: world.World, repository: repo.Repo) -> None:
        log.debug('Rendering tile sets', 'Repo._render_tiles')

        self.static_frame = gui.new_image(game_world.dimensions)

        for group_key, group_conf in game_world.tilesets.items():
            group_tile = repository.get_layer('tiles', group_key)
            group_sets = group_conf['sets']

            log.debug(f'Rendering {group_key} tiles', 'Repo._render_tiles')

            for set_conf in group_sets:
                if set_conf['start']['tile_units']:
                    start = (set_conf['start']['x']*settings.TILE_DIM[0], 
                        set_conf['start']['y']*settings.TILE_DIM[1])
                else:
                    start = (set_conf['start']['x'], set_conf['start']['y'])

                set_dim = (set_conf['dim']['w'], set_conf['dim']['h'])

                log.debug(f'Rendering group set at {start[0], start[1]} with dimensions {set_dim[0], set_dim[1]}', 'Repo._render_tiles')
                
                for i in range(set_dim[0]):
                    for j in range(set_dim[1]):
                        dim = (start[0] + settings.TILE_DIM[0]*i, 
                            start[1] + settings.TILE_DIM[1]*j)
                        self.static_frame.paste(group_tile, dim)

    def _render_struts(self, game_world: world.World, repository: repo.Repo,):
        log.debug('Rendering strut sets', 'Repo._render_tiles')
        struts = game_world.strutsets

        for group_key, group_conf in struts.items():
            group_strut = repository.get_layer('struts', group_key)
            group_sets = group_conf['sets']

            log.debug(f'Rendering {group_key} struts', 'Repo._render_struts')

            for set_conf in group_sets:
                if set_conf['start']['tile_units']:
                    start = (set_conf['start']['x']*settings.TILE_DIM[0], 
                        set_conf['start']['y']*settings.TILE_DIM[1])
                else:
                    start = (set_conf['start']['x'], set_conf['start']['y'])

                log.debug(f'Rendering group set at {start[0], start[1]}', 'Repo._render_struts')

                self.static_frame.paste(group_strut, start)
    
    def _render_static(self, game_world: world.World):
        self.world_frame = gui.new_image(game_world.dimensions)
        self.world_frame.paste(self.static_frame, (0,0))

    def _render_hero(self, game_world: world.World, repository: repo.Repo):
        hero_position = (int(game_world.hero['position']['x']), int(game_world.hero['position']['y']))
        hero_state, hero_frame = game_world.hero['state'], game_world.hero['frame']
        hero_frame = repository.get_sprite('hero', hero_state, hero_frame)      
        self.world_frame.paste(hero_frame, hero_position, hero_frame)

    