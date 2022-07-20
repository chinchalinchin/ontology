
import os
import yaml
import onta.settings as settings

def state(obj: str) -> dict:
    state_path = os.path.join(settings.STATE_DIR, f'{obj}.yaml')
    with open(state_path, 'r') as infile:
        conf = yaml.safe_load(infile)
    return conf

