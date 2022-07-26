
import onta.settings as settings
import onta.world as world
import onta.load.conf as conf

class HUD():

    # HUD will essentially be its own world. let view decide how it is rendered.

    slots = None
    mirrors = None

    def __init__(self, ontology_path: str = settings.DATA_DIR):
        config = conf.Conf(ontology_path)
        self._init_display(config)

    def _init_display(self, config: conf.Conf):
        pass
    
    def update(self, game_world: world.World):
        pass