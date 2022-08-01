import threading
import time
from typing import Tuple

import PySide6.QtWidgets as QtWidgets
from PIL import Image

import onta.interface as interface
import onta.device as device
import onta.view as view
import onta.control as control
import onta.settings as settings
import onta.world as world
import onta.load.repo as repo
import onta.util.logger as logger
import onta.util.helper as helper
import onta.util.cli as cli


log = logger.Logger('onta.main', settings.LOG_LEVEL)


def create(args) -> Tuple[
    control.Controller,
    world.World,
    view.Renderer,
    repo.Repo,
    interface.HUD,
    device.Device
]:
    log.debug('Pulling device information...', 'create')
    player_device = device.Device(
        args.width, 
        args.height
    )

    log.debug('Initializing controller...', 'create')
    controller = control.Controller(args.ontology)

    log.debug('Initializing asset repository...', 'create')
    asset_repository = repo.Repo(args.ontology)

    log.debug('Initializing game world...', 'create')
    game_world = world.World(args.ontology)

    log.debug('Initializing HUD...', 'create')
    headsup_display = interface.HUD(
        player_device, 
        args.ontology
    )

    log.debug('Initializing Menu...', 'create')
    menu = interface.Menu(
        player_device,
        args.ontology
    )

    log.debug('Initializing rendering engine...', 'create')
    render_engine = view.Renderer(
        game_world, 
        asset_repository, 
        player_device
    )

    return controller, game_world, render_engine, \
            asset_repository, headsup_display, player_device, menu


def start(ontology_path: str) -> None:
    cntl, wrld, eng, rep, hd, dv, mn = create(ontology_path)

    log.debug('Creating GUI...', 'start')
    app, vw = view.get_app(), view.get_view(dv)

    log.debug('Threading game...', 'start')
    game_loop = threading.Thread(
        target=do, 
        args=(vw,cntl,wrld,eng,rep,hd, mn), 
        daemon=True
    )

    log.debug('Starting game loop...', 'start')
    vw.show()
    game_loop.start()
    view.quit(app)


def render(
    ontology_path: str, 
    crop: bool, 
    layer: str, 
    hud_on: bool
) -> Image.Image:
    _, wrld, eng, rep, hd, _ = create(ontology_path)
    hd.hud_activated = hud_on
    return eng.render(wrld, rep, hd, crop, layer, hd)


def do(
    game_view: QtWidgets.QWidget, 
    controller: control.Controller, 
    game_world: world.World, 
    render_engine: view.Renderer, 
    asset_repository: repo.Repo,
    headsup_display: interface.HUD,
    menu: interface.Menu
) -> None:
    ms_per_frame = (1/settings.FPS)*1000

    while True:
        start_time = helper.current_ms_time()

        user_input = controller.poll()

        # # pre_update hook here
            # # need:
            # # scripts/npc.py:state_handler
            # # construct npc state from game world info
        # scripts.apply_scripts(game_world, 'pre_update')

        if user_input['menu']:
            menu.toggle_menu()
        
        if not menu.menu_activated:
            game_world.iterate(user_input)
            headsup_display.update(game_world)

        else:
            # TODO: catch result in variable
            menu.update(user_input)
            controller.consume_all()
            
            # TODO: pass menu result back to game world

        if user_input['hud']:
            headsup_display.toggle_hud()
            

        # # pre_render hook here
        # scripts.apply_scripts(game_world, 'pre_render')

        render_engine.view(
            game_world, 
            game_view, 
            headsup_display,
            menu,
            asset_repository
        )

        # # post_loop hook here
        # scripts.apply_scripts(game_world, 'post_loop')
        
        end_time = helper.current_ms_time()
        diff = end_time - start_time
        sleep_time = ms_per_frame - diff

        if sleep_time >= 0:
            log.infinite(f'Loop time delta: {diff} ms', 'do')
            log.infinite(f'Sleeping excess period - delta: {sleep_time}', 'do')
            time.sleep(sleep_time/1000)

def entrypoint() -> None:
    args = cli.parse_cli_args()

    if args.render:
        img = render(args.ontology, args.crop, args.layer, args.hud)
        img.save(args.render)
        return

    start(args)

if __name__=="__main__":
    entrypoint()
    