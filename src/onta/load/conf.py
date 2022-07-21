import os
import yaml

class Conf():

    conf_dir = None

    def __init__(self, data_dir):
        self.conf_dir = os.path.join(data_dir, 'conf')
    
    def configuration(self, obj: str) -> dict:
        conf_path = os.path.join(self.conf_dir, f'{obj}.yaml')
        with open(conf_path, 'r') as infile:
            conf = yaml.safe_load(infile)
        return conf
