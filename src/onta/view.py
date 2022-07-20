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

def render(game_world: world.World, view: QtWidgets.QWidget, repo: repo.Repo):
    view_frame = view.layout().itemAt(0).widget()
    view_frame.hide()

    _render_tiles(game_world, view, repo)
    _render_struts()

    view_frame.show()
    return view


def _render_tiles(game_world: world.World, view: QtWidgets.QWidget, repository: repo.Repo) -> QtWidgets.QWidget:
    log.debug('Rendering tile sets', '_render_tiles')
    frame = Image.new(settings.IMG_MODE, game_world.dimensions, settings.IMG_BLANK)

    tiles = game_world.tilesets

    for group_key, group_conf in tiles.items():
        group_tile = repository.get_asset('tiles', group_key)
        group_sets = group_conf['sets']
        log.debug(f'Rendering {group_key} tiles', 'render_tiles')

        for group_conf in group_sets:
            # group_conf measured in tiles, so scale by pixels per tile
            start = (group_conf['start']['x']*settings.TILE_DIM[0], 
                group_conf['start']['y']*settings.TILE_DIM[1])
            group_dim = (group_conf['dim']['w']*settings.TILE_DIM[0], 
                group_conf['dim']['h']*settings.TILE_DIM[1])

            log.debug(f'Rendering group set at ({start[0]}, {start[1]}) with dimensions ({group_dim[0], group_dim[1]})', '_render_tiles')
            
            for i in range(group_dim[0]):
                for j in range(group_dim[1]):
                    dim = (start[0]*i, start[1]*j, group_dim[0], group_dim[1])
                    print(dim)
                    frame.paste(group_tile, dim)

    view_frame = view.layout().itemAt(0).widget()

    qim = ImageQt(frame)
    pix = QtGui.QPixmap.fromImage(qim)
    view_frame.setPixmap(pix)
    return view

def _render_struts(game_world: world.World, view: QtWidgets.QWidget, repository: repo.Repo):
    view_frame = view.layout().itemAt(0).widget()
    frame = gui.qimage_to_image(view_frame.pixmap().toImage())
    
    # TODO: render struts....

    qim = ImageQt(frame)
    pix = QtGui.QPixmap.fromImage(qim)
    view_frame.setPixmap(pix)
    return view