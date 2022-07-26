
import onta.world as world
import onta.load.conf as conf

class HUD():

    display_frame = None
    slots = None
    mirrors = None

    def __init__(self, config: conf.Conf):
        self._init_display(config)

    def _init_display(config: conf.Conf):
        pass
    
    def update(game_world: world.World):
        pass