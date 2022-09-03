import threading
import time
from typing import Tuple

import PySide6.QtWidgets as QtWidgets
from PIL import Image

import onta.device as device
import onta.view as view
import onta.control as control
import onta.settings as settings
import onta.world as world

import onta.actuality.datum as datum

import onta.metaphysics.logger as logger
import onta.metaphysics.helper as helper
import onta.metaphysics.cli as cli

import onta.concrescence.qualia.noema as noema
import onta.concrescence.qualia.noesis as noesis

log = logger.Logger('onta.main', settings.LOG_LEVEL)


def create(args) -> Tuple[
    control.Controller,
    world.World,
    view.Renderer,
    datum.Totality,
    noema.SensoryQuale,
    noesis.NoeticQuale
]:
    log.debug(
        'Pulling device information...', 
        'create'
    )
    player_device = device.Device(
        args.width, 
        args.height
    )

    log.debug(
        'Initializing controller...', 
        'create'
    )
    controller = control.Controller(args.ontology)

    log.debug(
        'Initializing asset repository...', 
        'create'
    )
    data_totality = datum.Totality(args.ontology)

    log.debug(
        'Initializing game world...', 
        'create'
    )
    game_world = world.World(args.ontology)

    log.debug(
        'Initializing HUD...', 
        'create'
    )
    headsup_display = noema.SensoryQuale(
        player_device, 
        args.ontology
    )

    log.debug(
        'Initializing Menu...', 
        'create'
    )
    pause_menu = noesis.NoeticQuale(
        player_device,
        args.ontology
    )

    log.debug(
        'Initializing rendering engine...', 
        'create'
    )
    render_engine = view.Renderer(
        game_world, 
        data_totality, 
        player_device,
        args.debug
    )

    return controller, game_world, render_engine, \
            data_totality, headsup_display, pause_menu


def start(
    args
) -> None:
    cntl, wrld, eng, dat, nom, nos = create(args)

    log.debug('Creating GUI...', 'start')
    app, vw = view.get_app(), eng.get_view()

    log.debug('Threading game...', 'start')
    game_loop = threading.Thread(
        target=do, 
        args=(
            vw,
            cntl,
            wrld,
            eng,
            dat,
            nom,
            nos,
            args.debug
        ), 
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
    _, wld, eng, rep, hd, mn = create(args)
    hd.hud_activated = args.hud
    return eng.render(wld, rep, hd, mn, args.crop, args.layer)


def do(
    game_view: QtWidgets.QWidget, 
    controller: control.Controller, 
    game_world: world.World, 
    render_engine: view.Renderer, 
    data_totality: datum.Totality,
    display_quale: noema.SensoryQuale,
    pause_quale: noesis.NoeticQuale,
    debug: bool = False
) -> None:

    loading = True
    ms_per_frame = (1/settings.FPS)*1000
    no_delays_per_yield = 16
    max_frame_skips = 5
    over_sleep, no_delays, excess = 0, 0, 0
    start_time = helper.current_ms_time()

    while True:

        if not loading:

            game_input, menu_input = controller.poll(
                pause_quale.quale_activated
            )

            # # pre_update hook here
                # # need:
                # # scripts/npc.py:state_handler
                # # construct npc state from game world info
            # scripts.apply_scripts(game_world, 'pre_update')

            if not pause_quale.quale_activated and game_input.menu:
                pause_quale.toggle_quale()
            
            if not pause_quale.quale_activated:
                game_world.iterate(game_input)
                display_quale.update(game_world)

            else:
                # TODO: catch result in variable
                pause_quale.update(
                    menu_input,
                    game_world
                )
                
                if not pause_quale.quale_activated:
                    controller.consume_all()

                # TODO: pass menu result back to game world
                # for updating hero state


            if game_input.get('hud'):
                display_quale.toggle_hud()
                

            # # pre_render hook here
            # scripts.apply_scripts(game_world, 'pre_render')

            if debug:
                render_engine.view(
                    game_world, 
                    game_view, 
                    display_quale,
                    pause_quale,
                    data_totality,
                    game_input
                )
            else:
                render_engine.view(
                    game_world, 
                    game_view, 
                    display_quale,
                    pause_quale,
                    data_totality
                )

            # # post_loop hook here
            # scripts.apply_scripts(game_world, 'post_loop')
            
            end_time = helper.current_ms_time()
            diff = end_time - start_time
            sleep_time = ms_per_frame - diff - over_sleep

            if sleep_time >= 0:
                log.timer(f'Loop iteration too short -  delta: {sleep_time} ms')
                time.sleep(sleep_time/1000)
                over_sleep = helper.current_ms_time() - end_time - sleep_time

            else:
                log.timer(f'Loop iteration too long - delta: {sleep_time} ms')
                excess -= sleep_time
                no_delays += 1

                if no_delays >= no_delays_per_yield:
                    log.timer(f'Yielding thread')
                    time.sleep(0)
                    no_delays = 0

            start_time = helper.current_ms_time()
            skips = 0
            while ( (excess>ms_per_frame) and (skips < max_frame_skips) ):
                log.timer(f'Updating world to catch up')
                excess -= ms_per_frame
                game_world.iterate(game_input)
                skips += 1

        else:
            # TODO: loading functionality and screen...

            time.sleep(1)
            loading = False
            

def entrypoint() -> None:
    args = cli.parse_cli_args()

    if args.render:
        img = render(args)
        img.save(args.render)
        return

    start(args)

if __name__=="__main__":
    entrypoint()
    