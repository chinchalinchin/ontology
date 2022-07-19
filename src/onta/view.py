import sys

from PySide6 import QtWidgets, QtGui

from onta import settings

APPLICATION = None

def init():
    return QtWidgets.QApplication([])    

def quit(app):
    sys.exit(app.exec_())

def view():
    view_widget = QtWidgets.QWidget()
    view_widget.resize(settings.DEFAULT_WIDTH, settings.DEFAULT_HEIGHT)
    center = QtGui.QScreen.availableGeometry(
        QtWidgets.QApplication.primaryScreen()).center()
    geo = view_widget.frameGeometry()
    geo.moveCenter(center)
    view_widget.move(geo.topLeft())
    return view_widget

def render(world_state: dict):
    pass