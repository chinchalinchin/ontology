import argparse

from onta.metaphysics \
    import settings


def parse_cli_args():
    # TODO: implement hierarchy of commands with subparsers:
    #       onta start
    #               --ontology <>
    #               --debug
    #       onta render
    #               --ontology <>
    #               --render <>
    #               --layer <>
    #               --hud <>
    #               --crop
    parser = argparse.ArgumentParser(description="An LPC compliant game engine")
    parser.add_argument(
        '-o',
        '--o',
        '-ontology',
        '--ontology',
        nargs="?",
        type=str,
        dest='ontology',
        default=str(settings.DEFAULT_DIR),
        help="Path to an ontology. If passed in, this path will override the default directory used for assets and configuration"
    )
    parser.add_argument(
        '-r',
        '--r',
        '-render',
        '--render',
        nargs="?",
        type=str,
        dest="render",
        help="Path to a rendering location. If passed in, the game loop will not start and the world will be rendered to location provided."
    )
    parser.add_argument(
        '-l',
        '--l',
        '-layer',
        '--layer',
        nargs="?",
        type=str,
        dest="layer",
        help="Name of the layer to render."
    )
    parser.add_argument(
        '-cr',
        '--cr',
        '-crop',
        '--crop',
        action='store_true',
        dest="crop",
        help="If passed in, rendered game world frame will be cropped to screen dimensions."
    )
    parser.add_argument(
        '-db',
        '--db',
        '-debug',
        '--debug',
        action='store_true',
        dest="debug",
        help="Start the game loop in debug mode"
    )
    parser.add_argument(
        '-sw',
        '--sw',
        '-screen-width',
        '--screen-width',
        nargs="?",
        type=int,
        dest='width',
        default=settings.SCREEN_DEFAULT_WIDTH,
        help="Set the screen width"
    )
    parser.add_argument(
        '-sh',
        '--sh',
        '-screen-height',
        '--screen-height',
        nargs="?",
        type=int,
        dest='height',
        default=settings.SCREEN_DEFAULT_HEIGHT,
        help="Set the screen height"
    )
    parser.add_argument(
        '-hud',
        '--hud',
        '-heads-up',
        '--heads-up',
        action='store_true',
        dest="hud",
        help="If passed in,the HUD will be added to the render"
    )
    return parser.parse_args()