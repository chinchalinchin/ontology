
import os
import yaml
import onta.settings as settings

def get_state(obj: str) -> dict:
    state_path = os.path.join(settings.STATE_DIR, f'{obj}.yaml')
    with open(state_path, 'r') as infile:
        conf = yaml.safe_load(infile)
    return conf

def save_state(obj: str, state: dict):
    pass