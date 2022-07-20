import os
import yaml
import onta.settings as settings

SHEET_SIZE = (832, 1344)
"""Dimensions of spritesheets"""

def configuration(obj: str) -> dict:
    conf_path = os.path.join(settings.CONF_DIR, f'{obj}.yaml')
    with open(conf_path, 'r') as infile:
        conf = yaml.safe_load(infile)
    return conf

