
import onta.settings as settings
import onta.world as world
import onta.load.conf as conf

class HUD():

    # HUD will essentially be its own world. let view decide how it is rendered.

    slots = None
    mirrors = None

    def __init__(self, ontology_path: str = settings.DEFAULT_DIR):
        config = conf.Conf(ontology_path)
        self._init_slots(config)

    def _init_slots(self, config: conf.Conf):
        pass

    def _init_mirrors(self, config: conf.Conf):
        pass
    
    def update(self, game_world: world.World):
        game_world.hero['slots']
        game_world.hero['bag']
        game_world.hero['ammo']
        game_world.hero['health']['current'], game_world.hero['health']['max']

        for slot_key, slot in game_world.hero['slots']:
            pass
