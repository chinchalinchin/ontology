import threading

import PySide6.QtWidgets as QtWidgets

import onta.view as view
import onta.control as control
import onta.settings as settings
import onta.world as world

import onta.load.repo as repo

import onta.util.logger as logger

log = logger.Logger('ontology.onta.main', settings.LOG_LEVEL)

repository = repo.Repo() 
game_world = world.World()

def be():
    app, game_view = view.init(), view.view()
    game_loop = threading.Thread(target=do, args=(game_view,), daemon=True)
    game_loop.start()
    view.quit(app)

def do(game_view: QtWidgets.QWidget):
    while True:
        user_input = control.poll()
        log.debug(f'User Input: {user_input}', 'loop')

        game_world.iterate(user_input)

        view.render(game_world, game_view, repository)

if __name__=="__main__":
    be()