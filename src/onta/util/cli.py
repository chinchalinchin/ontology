
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
    return parser.parse_args()