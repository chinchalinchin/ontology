
import argparse

import onta.settings as settings


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
        default=str(settings.DEFAULT_DIR),
    )
    parser.add_argument(
        '-r',
        '--r',
        '-render',
        '--render',
        nargs="?",
        type=str,
        dest="render",
    )
    parser.add_argument(
        '-l',
        '--l',
        '-layer',
        '--layer',
        nargs="?",
        type=str,
        dest="layer"
    )
    parser.add_argument(
        '-cr',
        '--cr',
        '-crop',
        '--crop',
        action='store_true',
        dest="crop"
    )
    parser.add_argument(
        '-db',
        '--db',
        '-debug',
        '--debug',
        action='store_true',
        dest="debug"
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
    )
    parser.add_argument(
        '-hud',
        '--hud',
        '-heads-up',
        '--heads-up',
        action='store_true',
        dest="hud"
    )
    return parser.parse_args()