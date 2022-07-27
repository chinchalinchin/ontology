
import onta.settings as settings
import onta.device as device
import onta.world as world
import onta.load.conf as conf
import onta.load.state as state

SLOTS_TOTAL = 4

class HUD():

    # HUD will essentially be its own world. let view decide how it is rendered.

    hud_conf = None
    activated = True
    media_size = None
    styles = None
    sizes = None
    breakpoints = None
    slots = None

    @staticmethod
    def format_breakpoints(break_points: list) -> list:
        return [
            (break_point['w'], break_point['h']) 
                for break_point in break_points
        ]

    def __init__(self, player_device: device.Device, ontology_path: str = settings.DEFAULT_DIR):
        config = conf.Conf(ontology_path).load_interface_configuration()
        state_ao = state.State(ontology_path).get_state('dynamic')
        self.styles = config.get('hud').get('styles')
        self._init_conf(config)
        self._find_media_size(player_device)
        self._init_positions(player_device)
        self._init_slots(state_ao)
        self._init_mirrors(state_ao)


    def _init_conf(self, config: conf.Conf):
        self.styles = config['hud']['styles']
        self.hud_conf = {
            key: val
            for key, val in config['hud'].items()
            if key != 'styles'
        }
        self.sizes = config['sizes']
        self.breakpoints = config['breakpoints']


    def _find_media_size(self, player_device: device.Device):
        breakpoints = self.format_breakpoints(self.breakpoints)
        dim = player_device.dimensions
        for i, break_point in enumerate(breakpoints):
            if dim[0] < break_point[0] and dim[1] < break_point[1]:
                self.media_size = self.sizes[i]
                break
        self.media_size = self.sizes[len(self.sizes)-1]


    def _init_positions(self, player_device:device.Device):
         # note the difference between the 'slots' key in the hud_conf dict 
        # and the self.slots property. the first represents image configuration properties
        # the second represents player state information

        slot_styles = self.styles[self.media_size]['slots']
        x_margins = settings.SLOT_MARGINS*player_device.dimensions[0]
        y_margins = settings.SLOT_MARGINS*player_device.dimensions[1]

        if slot_styles['stack'] == 'horizontal':
            if slot_styles['alignment']['horizontal'] == 'right':
                leftcap_width = self.hud_conf[self.media_size]['slots']['left']['image']['size']['w']
                buffer_width = self.hud_conf[self.media_size]['slots']['buffer']['image']['size']['w']
                slot_width = self.hud_conf[self.media_size]['slots']['empty']['image']['size']['w']
                rightcap_width = self.hud_conf[self.media_size]['slots']['right']['image']['size']['w']
                x_start = player_device.dimensions[0] \
                    - x_margins \
                    - SLOTS_TOTAL*slot_width \
                    - (SLOTS_TOTAL-1)*buffer_width \
                    - leftcap_width - rightcap_width
            else:
                x_start = x_margins
            
            if slot_styles['alignment']['vertical'] == 'top':
                y_start = y_margins
            else:
                slot_height = self.hud_conf[self.media_size]['slots']['empty']['image']['size']['h']
                y_start = player_device.dimensions[1] \
                    - y_margins \
                    - slot_height


    def _init_slots(self, state_ao):
        self.slots = state_ao.get('hero').get('slots')


    def _init_mirrors(self, state_ao: state.State):
        pass


    def slot_frame_map(self):
        return {
            key: 'empty' if val is None else 'equipped' 
            for key, val in self.slots.items()
        }


    def update(self, game_world: world.World):
        self.slots = game_world.hero['slots']


    def toggle(self) -> None:
        self.activated = not self.activated
