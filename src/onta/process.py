import threading
import time
from typing \
    import Tuple
from PIL \
    import Image
from PySide6 \
    import QtWidgets

from onta \
    import gestalt, will, world
from onta.actuality \
    import datum
from onta.metaphysics \
    import device, logger, cli, settings
from onta.qualia \
    import intrinsic, extrinsic

log = logger.Logger(
    'onta.process', 
    settings.LOG_LEVEL
)


def current_ms_time():
    return round(time.time() * 1000)
    
def create(args) -> Tuple[
    will.Will,
    world.World,
    gestalt.Renderer,
    datum.Totality,
    extrinsic.ExtrinsicQuale,
    intrinsic.IntrinsicQuale
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
    player_will = will.Will(args.ontology)

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
    ex_quale = extrinsic.ExtrinsicQuale(
        player_device, 
        args.ontology
    )

    log.debug(
        'Initializing Menu...', 
        'create'
    )
    in_quale = intrinsic.IntrinsicQuale(
        player_device,
        args.ontology
    )

    log.debug(
        'Initializing rendering engine...', 
        'create'
    )
    renderer = gestalt.Renderer(
        game_world, 
        data_totality, 
        player_device,
        args.debug
    )

    return player_will, game_world, renderer, \
            data_totality, ex_quale, in_quale


def start(
    args
) -> None:
    player_will, game_world, renderer, \
        data_totality, ex_quale, in_quale = create(args)

    log.debug(
        'Creating GUI...', 
        'start'
    )
    app, game_view = (
        gestalt.get_app(), 
        renderer.get_view()
    )

    log.debug(
        'Threading game...',
        'start'
    )
    game_loop = threading.Thread(
        target=do, 
        args=(
            game_view, 
            player_will, 
            game_world, 
            renderer, 
            data_totality, 
            ex_quale, 
            in_quale, 
            args.debug
        ), 
        daemon=True
    )

    log.debug(
        'Starting game loop...', 
        'start'
    )
    game_view.show()
    game_loop.start()
    gestalt.quit(app)


def render(
    args
) -> Image.Image:
    # TODO: use args.width and args.height to adjust crop box for render method...
    _, game_world, renderer, \
        data_totality, ex_quale, in_quale = create(args)

    ex_quale.quale_activated = args.hud

    return renderer.render(
        game_world, 
        data_totality, 
        ex_quale, 
        in_quale, 
        args.crop, 
        args.layer
    )


def do(
    game_view: QtWidgets.QWidget, 
    player_will: will.Will, 
    game_world: world.World, 
    render_engine: gestalt.Renderer, 
    data_totality: datum.Totality,
    display_quale: extrinsic.ExtrinsicQuale,
    pause_quale: intrinsic.IntrinsicQuale,
    debug: bool = False
) -> None:

    loading = True
    ms_per_frame = ( 1 / settings.FPS ) * 1000
    no_delays_per_yield = 16
    max_frame_skips = 5
    over_sleep, no_delays, excess = 0, 0, 0
    start_time = current_ms_time()

    while True:

        if not loading:

            game_input, menu_input = player_will.poll(
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
                    player_will.consume_all()

                # TODO: pass menu result back to game world
                # for updating hero state


            if game_input.get('hud'):
                display_quale.toggle_quale()
                

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
            
            end_time = current_ms_time()
            diff = end_time - start_time
            sleep_time = ms_per_frame - diff - over_sleep

            if sleep_time >= 0:
                log.timer(f'Loop iteration too short -  delta: {sleep_time} ms')
                time.sleep( sleep_time / 1000 )
                over_sleep = current_ms_time() - end_time - sleep_time

            else:
                log.timer(f'Loop iteration too long - delta: {sleep_time} ms')
                excess -= sleep_time
                no_delays += 1

                if no_delays >= no_delays_per_yield:
                    log.timer(f'Yielding thread')
                    time.sleep(0)
                    no_delays = 0

            start_time = current_ms_time()
            skips = 0
            
            while ( 
                ( excess > ms_per_frame ) and \
                ( skips < max_frame_skips ) 
            ):
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
    