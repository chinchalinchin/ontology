import sys
from PySide6 import QtWidgets, QtGui

import onta.view as view

def be():
    app = QtWidgets.QApplication([])
    game = view.view()
    game.resize(800, 800)
    center = QtGui.QScreen.availableGeometry(
        QtWidgets.QApplication.primaryScreen()).center()
    geo = game.frameGeometry()
    geo.moveCenter(center)
    game.move(geo.topLeft())
    game.show()
    sys.exit(app.exec_())

if __name__=="__main__":
    be()