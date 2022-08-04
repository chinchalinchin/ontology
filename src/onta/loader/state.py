
import os
import munch
import yaml

class State():

    state_dir = None

    def __init__(self, data_dir):
        self.state_dir = os.path.join(
            data_dir, 
            'state'
        )

    def get_state(self, obj: str) -> dict:
        state_path = os.path.join(
            self.state_dir, 
            f'{obj}.yaml'
        )
        with open(state_path, 'r') as infile:
            conf = munch.munchify(
                yaml.safe_load(infile)
            )
        return conf

    def save_state(self, obj: str, state: dict):
        pass