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


def create():
    log.debug('Initializing controller...', 'create')
    controller = control.Controller()

    log.debug('Initializing asset repository...', 'create')
    asset_repository = repo.Repo()
    
    log.debug('Calculating state frames from sheets metadata...', 'create')
    sprite_state_conf = asset_repository.enumerate_sprite_state_frames()

    log.debug('Initializing game world...', 'create')
    game_world = world.World(sprite_state_conf)

    log.debug('Initializing rendering engine...', 'create')
    render_engine = view.Renderer(game_world, asset_repository)
    return controller, game_world, render_engine, asset_repository

def start():
    log.debug('Creating GUI...', 'start')
    app, vw = view.init(), view.view()
    cntl, wrld, eng, rep = create()

    log.debug('Threading game...', 'start')
    game_loop = threading.Thread(
        target=do, 
        args=(vw,cntl,wrld,eng,rep), 
        daemon=True
    )

    log.debug('Starting game loop...', 'start')
    vw.show()
    game_loop.start()
    view.quit(app)

def do(
    game_view: QtWidgets.QWidget, 
    controller: control.Controller, 
    game_world: world.World, 
    render_engine: view.Renderer, 
    asset_repository: repo.Repo
):
    ms_per_frame = (1/settings.FPS)*1000

    while True:
        start_time = helper.current_ms_time()

        user_input = controller.poll()
        game_world.iterate(user_input)
        render_engine.render(game_world, game_view, asset_repository)

        end_time = helper.current_ms_time()
        diff = end_time - start_time
        sleep_time = ms_per_frame - diff

        if sleep_time >= 0:
            log.verbose(f'Loop time delta: {diff} ms', 'do')
            log.verbose(f'Sleeping excess period - delta: {sleep_time}', 'do')
            time.sleep(sleep_time/1000)

if __name__=="__main__":
    start()