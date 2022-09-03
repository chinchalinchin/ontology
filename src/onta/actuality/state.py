
import os

import munch
import yaml

import onta.settings as settings

class State():

    state_dir = None

    def __init__(
        self, 
        data_dir = settings.DEFAULT_DIR
    ) -> None:
        self.state_dir = os.path.join(data_dir, *settings.STATE_PATH)


    def get_state(
        self, 
        state_type: str
    ) -> munch.Munch:
        state_path = os.path.join(self.state_dir, f'{state_type}.yaml')
        with open(state_path, 'r') as infile:
            conf = munch.munchify(
                yaml.safe_load(infile)
            )
        return conf

    def save_state(
        self, 
        obj: str, 
        state: munch.Munch
    ) -> None:
        pass