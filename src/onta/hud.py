
import onta.settings as settings
import onta.device as device
import onta.world as world
import onta.load.conf as conf

class HUD():

    # HUD will essentially be its own world. let view decide how it is rendered.

    activated = True
    media_size = None
    slots = None
    mirrors = None
    display_conf = None
    slot_conf = None
    mirrors_conf = None
    avatars_conf = None

    @staticmethod
    def format_breakpoints(break_points: list) -> list:
        return [
            (break_point['w'], break_point['h']) 
                for break_point in break_points
        ]

    def __init__(self, player_device: device.Device, ontology_path: str = settings.DEFAULT_DIR):
        config = conf.Conf(ontology_path).load_interface_configuration()
        sizes = config.get('sizes')
        breakpoints = self.format_breakpoints(config['breakpoints'])
        self._find_media_size(player_device, breakpoints, sizes)
        self._init_conf(config)
        self._init_slots()


    def _find_media_size(self, player_device: device.Device, breakpoints: list, sizes: list):
        dim = player_device.dimensions
        for i, break_point in enumerate(breakpoints):
            if dim[0] < break_point[0] and dim[1] < break_point[1]:
                self.media_size = sizes[i]
                break
        self.media_size = sizes[len(sizes)-1]


    # don't know if i need this..
    def _init_conf(self, config: conf.Conf):
        hud_conf = config.get('hud')
        self.display_conf = hud_conf[self.media_size]['display']
        self.slot_conf = hud_conf[self.media_size]['slot']
        self.mirrors_conf = hud_conf[self.media_size]['mirrors']
        self.avatars_conf = hud_conf[self.media_size]['avatars']

    def _init_slots(self):    
        # slots = {
        #   'cast':
        #   'thrust':
        #   'slash':
        #   'shoot':
        # }
        pass

    def _init_mirrors(self):
        pass
    
    def update(self, game_world: world.World):
        game_world.hero['slots']
        game_world.hero['bag']
        game_world.hero['ammo']
        game_world.hero['health']['current'], game_world.hero['health']['max']

        for slot_key, slot in game_world.hero['slots'].items():
            pass

    def toggle(self) -> None:
        self.activated = not self.activated
