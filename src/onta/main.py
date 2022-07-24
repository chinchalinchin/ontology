import argparse
import threading
import time
import sys

import PySide6.QtWidgets as QtWidgets

import onta.view as view
import onta.control as control
import onta.settings as settings
import onta.world as world
import onta.load.repo as repo
import onta.load.conf as conf
import onta.load.state as state
import onta.util.logger as logger
import onta.util.helper as helper

log = logger.Logger('onta.main', settings.LOG_LEVEL)


def parse_cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-o',
        '--o',
        '-ontology',
        '--ontology',
        nargs="?",
        type=str,
        dest='ontology',
        default=str(settings.DATA_DIR),
    )
    return parser.parse_args()

def create(ontology_path: str):
    log.debug('Intializing configuration access object...', 'create')
    config = conf.Conf(ontology_path)

    log.debug('Initializing state access object...', 'create')
    state_ao = state.State(ontology_path)

    log.debug('Initializing controller...', 'create')
    controller = control.Controller(config)

    log.debug('Initializing asset repository...', 'create')
    asset_repository = repo.Repo(config)

    log.debug('Initializing game world...', 'create')
    game_world = world.World(config, state_ao)

    log.debug('Initializing rendering engine...', 'create')
    render_engine = view.Renderer(game_world, asset_repository)
    return controller, game_world, render_engine, asset_repository

def start(ontology_path: str):
    log.debug('Creating GUI...', 'start')
    app, vw = view.init(), view.view()
    cntl, wrld, eng, rep = create(ontology_path)

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

        # # pre_update hook here
            # # need:
            # # scripts/npc.py:state_handler
            # # construct npc state from game world info
        # scripts.apply_scripts(game_world, 'pre_update')

        game_world.iterate(user_input)

        # # pre_render hook here
        # scripts.apply_scripts(game_world, 'pre_render')

        render_engine.render(game_world, game_view, asset_repository)

        # # post_render hook here
        # scripts.apply_scripts(game_world, 'post_render')
        
        end_time = helper.current_ms_time()
        diff = end_time - start_time
        sleep_time = ms_per_frame - diff

        if sleep_time >= 0:
            log.infinite(f'Loop time delta: {diff} ms', 'do')
            log.infinite(f'Sleeping excess period - delta: {sleep_time}', 'do')
            time.sleep(sleep_time/1000)

def entrypoint():
    args = parse_cli_args()
    start(args.ontology)

if __name__=="__main__":
    entrypoint()
    