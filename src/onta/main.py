import threading
import time
from typing import Tuple

import PySide6.QtWidgets as QtWidgets
from PIL import Image
from jinja2 import PrefixLoader

import onta.device as device
import onta.view as view
import onta.control as control
import onta.settings as settings
import onta.world as world

import onta.engine.senses.hud as hud
import onta.engine.senses.menu as menu

import onta.loader.repo as repo

import onta.util.logger as logger
import onta.util.helper as helper
import onta.util.cli as cli

log = logger.Logger('onta.main', settings.LOG_LEVEL)


def create(args) -> Tuple[
    control.Controller,
    world.World,
    view.Renderer,
    repo.Repo,
    hud.HUD,
    device.Device,
    menu.Menu
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
    headsup_display = hud.HUD(
        player_device, 
        args.ontology
    )

    log.debug('Initializing Menu...', 'create')
    pause_menu = menu.Menu(
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
            asset_repository, headsup_display, player_device, pause_menu


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
    args
) -> Image.Image:
    # TODO: use args.width and args.height to adjust crop box for render method...
    _, wld, eng, rep, hd, _, mn = create(args)
    hd.hud_activated = args.hud
    return eng.render(wld, rep, hd, mn, args.crop, args.layer)


def do(
    game_view: QtWidgets.QWidget, 
    controller: control.Controller, 
    game_world: world.World, 
    render_engine: view.Renderer, 
    asset_repository: repo.Repo,
    headsup_display: hud.HUD,
    pause_menu: menu.Menu
) -> None:
    ms_per_frame = (1/settings.FPS)*1000
    no_delays_per_yield = 16
    max_frame_skips = 5
    over_sleep, no_delays, excess = 0, 0, 0

    start_time = helper.current_ms_time()

    while True:

        user_input = controller.poll()

        # # pre_update hook here
            # # need:
            # # scripts/npc.py:state_handler
            # # construct npc state from game world info
        # scripts.apply_scripts(game_world, 'pre_update')

        if user_input.menu:
            pause_menu.toggle_menu()
        
        if not pause_menu.menu_activated:
            game_world.iterate(user_input)
            headsup_display.update(game_world)

        else:
            # TODO: catch result in variable
            pause_menu.update(user_input)
            controller.consume_all()
            
            # TODO: pass menu result back to game world
            # for updating hero state

        if user_input.get('hud'):
            headsup_display.toggle_hud()
            

        # # pre_render hook here
        # scripts.apply_scripts(game_world, 'pre_render')

        render_engine.view(
            game_world, 
            game_view, 
            headsup_display,
            pause_menu,
            asset_repository
        )

        # # post_loop hook here
        # scripts.apply_scripts(game_world, 'post_loop')
        
        end_time = helper.current_ms_time()
        diff = end_time - start_time
        sleep_time = ms_per_frame - diff - over_sleep

        if sleep_time >= 0:
            log.maximum_overdrive(f'Loop iteration too short -  delta: {diff} ms', 'do')
            log.maximum_overdrive(f'Sleeping excess period - delta: {sleep_time}', 'do')
            time.sleep(sleep_time/1000)
            over_sleep = helper.current_ms_time() - end_time - sleep_time
        else:
            log.maximum_overdrive(f'Loop iteration too long - delta: {sleep_time}', 'do')
            excess -= sleep_time
            no_delays += 1
            if no_delays >= no_delays_per_yield:
                log.maximum_overdrive(f'Yielding thread', 'do')
                time.sleep(0)
                no_delays = 0

        start_time = helper.current_ms_time()
        skips = 0
        while ( (excess>ms_per_frame) and (skips < max_frame_skips)):
            log.maximum_overdrive(f'Updating world to catch up', 'do')
            excess -= ms_per_frame
            game_world.iterate(user_input)
            skips += 1
            

def entrypoint() -> None:
    args = cli.parse_cli_args()

    if args.render:
        img = render(args)
        img.save(args.render)
        return

    start(args)

if __name__=="__main__":
    entrypoint()
    