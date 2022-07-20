import threading
import time

import PySide6.QtWidgets as QtWidgets

import onta.view as view
import onta.control as control
import onta.settings as settings
import onta.world as world

import onta.load.repo as repo

import onta.util.logger as logger
import onta.util.helper as helper

log = logger.Logger('ontology.onta.main', settings.LOG_LEVEL)

asset_repository = repo.Repo() 
game_world = world.World()
render_engine = view.Renderer(game_world, asset_repository)

def be():
    app, game_view = view.init(), view.view()
    game_loop = threading.Thread(target=do, args=(game_view,), daemon=True)
    game_view.show()
    game_loop.start()
    view.quit(app)

def do(game_view: QtWidgets.QWidget):
    ms_per_frame = (1/settings.FPS)*1000

    while True:
        start_time = helper.current_ms_time()

        user_input = control.poll()
        world_state = game_world.iterate(user_input)
        render_engine.render(world_state, game_view, asset_repository)

        end_time = helper.current_ms_time()
        diff = end_time - start_time
        sleep_time = ms_per_frame - diff

        if sleep_time >= 0:
            log.verbose(f'Loop time delta: {diff} ms', 'do')
            log.verbose(f'Sleeping excess period - delta: {sleep_time}', 'do')
            time.sleep(sleep_time/1000)

if __name__=="__main__":
    be()