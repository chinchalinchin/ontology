
import onta.settings as settings
import onta.load.state as state
import onta.util.logger as logger


log = logger.Logger('ontology.onta.world', settings.LOG_LEVEL)

class World():


    def __init__(self):
        self._init_static_layer()

    def _init_static_layer(self):
        static_conf = state.state('static')
        self.dimensions = (static_conf['dim']['w']*settings.TILE_DIM[0], 
            static_conf['dim']['h']*settings.TILE_DIM[1])
        self.tilesets = static_conf['tiles']
        self.strutsets = static_conf['struts']

        log.debug(f'Initialized static world layer with dimensions {self.dimensions}', 'world.World._init_static_layer')

    def iterate(self, user_input: dict) -> dict:
        return {}