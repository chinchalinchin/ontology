
import onta.load.state as state

class World():


    def __init__(self):
        self._init_static_layer()

    def _init_static_layer(self):
        static_conf = state.state('static')
        self.dimensions = (static_conf['dim']['w'], static_conf['dim']['h'])
        self.tilesets = static_conf['tiles']


    def iterate(self, user_input: dict):
        pass