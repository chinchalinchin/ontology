import sys

from PySide6 import QtWidgets, QtGui
from PIL import Image
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

    view_widget.resize(settings.DEFAULT_WIDTH, settings.DEFAULT_HEIGHT)
    view_layout.addWidget(view_frame)
    view_widget.setLayout(view_layout)

    center = QtGui.QScreen.availableGeometry(
        QtWidgets.QApplication.primaryScreen()).center()
    geo = view_widget.frameGeometry()
    geo.moveCenter(center)
    view_widget.move(geo.topLeft())

    return view_widget

class Renderer():
    world_frame = None

    def __init__(self, static_world, repository):
        # no references are kept to static_world, repository
        # they pass through and return to main.py
        self._render_tiles(static_world, repository)
        self._render_struts(static_world, repository)

    def render(self, game_world: world.World, view_widget: QtWidgets.QWidget, repo: repo.Repo):
        view_frame = view_widget.layout().itemAt(0).widget() 
        view_frame.hide()
        # frame = gui.qimage_to_image(view_frame.pixmap().toImage())
   
        self._render_objects()

        qim = ImageQt(self.world_frame)
        pix = QtGui.QPixmap.fromImage(qim)
        view_frame.setPixmap(pix)
        view_frame.show()

        return view_widget


    def _render_tiles(self, game_world: world.World, repository: repo.Repo) -> None:
        log.debug('Rendering tile sets', 'Repo._render_tiles')

        self.world_frame = gui.new_image(game_world.dimensions)
        tiles = game_world.tilesets

        for group_key, group_conf in tiles.items():
            group_tile = repository.get_asset('tiles', group_key)
            group_sets = group_conf['sets']

            log.debug(f'Rendering {group_key} tiles', 'Repo._render_tiles')

            for set_conf in group_sets:
                # group_conf measured in tiles, so scale by pixels per tile
                start = (set_conf['start']['x']*settings.TILE_DIM[0], 
                    set_conf['start']['y']*settings.TILE_DIM[1])
                set_dim = (set_conf['dim']['w'], set_conf['dim']['h'])

                log.debug(f'Rendering group set at {start[0], start[1]} with dimensions {set_dim[0], set_dim[1]}', 'Repo._render_tiles')
                
                for i in range(set_dim[0]):
                    for j in range(set_dim[1]):
                        dim = (start[0]*i, start[1]*j)
                        self.world_frame.paste(group_tile, dim)

    def _render_struts(self, game_world: world.World, repository: repo.Repo,):
        pass

    def _render_objects(self):
        pass

    