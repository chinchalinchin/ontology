import threading
import time

import PySide6.QtWidgets as QtWidgets
from PIL import Image

import onta.hud as hud
import onta.view as view
import onta.control as control
import onta.settings as settings
import onta.world as world
import onta.load.repo as repo
import onta.load.conf as conf
import onta.load.state as state
import onta.util.logger as logger
import onta.util.helper as helper
import onta.util.cli as cli

log = logger.Logger('onta.main', settings.LOG_LEVEL)


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

    log.debug('Initializing HUD...', 'create')
    headsup_display = hud.HUD()
    return controller, game_world, render_engine, asset_repository, headsup_display

def start(ontology_path: str):
    log.debug('Creating GUI...', 'start')
    app, vw = view.get_app(), view.get_view()
    cntl, wrld, eng, rep, hd = create(ontology_path)

    log.debug('Threading game...', 'start')
    game_loop = threading.Thread(
        target=do, 
        args=(vw,cntl,wrld,eng,rep,hd), 
        daemon=True
    )

    log.debug('Starting game loop...', 'start')
    vw.show()
    game_loop.start()
    view.quit(app)

def render(ontology_path: str, crop: bool, layer: str) -> Image.Image:
    _, wrld, eng, rep, hd = create(ontology_path)
    return eng.render(wrld, rep, crop, layer)


def do(
    game_view: QtWidgets.QWidget, 
    controller: control.Controller, 
    game_world: world.World, 
    render_engine: view.Renderer, 
    asset_repository: repo.Repo,
    headsup_display: hud.HUD
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

        # hud.update(game_world)

        # # pre_render hook here
        # scripts.apply_scripts(game_world, 'pre_render')

        render_engine.view(game_world, game_view, asset_repository)

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
    args = cli.parse_cli_args()

    if args.render:
        img = render(args.ontology, args.crop, args.layer)
        img.save(args.render)
        return

    start(args.ontology)

if __name__=="__main__":
    entrypoint()
    