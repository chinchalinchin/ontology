import munch
import os
import yaml

from onta.metaphysics \
    import settings

class State():
    def __init__(
        self, 
        data_dir = settings.DEFAULT_DIR
    ) -> None:
        self.state_conf = munch.Munch({})
        self.state_dir = os.path.join(
            data_dir, 
            *settings.STATE_PATH
        )


    def get_state(
        self, 
        state_type: str
    ) -> munch.Munch:
        if self.state_conf.get(state_type) is None:
            state_path = os.path.join(
                self.state_dir, 
                f'{state_type}.yaml'
            )
            
            with open(state_path, 'r') as infile:
                setattr(
                    self.state_conf,
                    state_type,
                    munch.munchify(
                        yaml.safe_load(infile)
                    )
                )

        return self.state_conf.get(state_type)


    def save_state(
        self, 
        obj: str, 
        state: munch.Munch
    ) -> None:
        pass