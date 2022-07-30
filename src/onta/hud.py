
import onta.settings as settings
import onta.device as device
import onta.world as world
import onta.load.conf as conf
import onta.load.state as state
import onta.util.logger as logger

log = logger.Logger('onta.hud', settings.LOG_LEVEL)

SLOT_STATES = [ 'cast', 'shoot', 'thrust', 'slash' ]
MIRROR_PADDING = 0.005

class HUD():

    # HUD will essentially be its own world. let view decide how it is rendered.

    hud_conf = {}
    styles = {}
    properties = {}
    breakpoints = {}
    slots = {}
    mirrors = {}
    sizes = []
    slot_rendering_points = []
    mirror_rendering_points = []
    activated = True
    media_size = None

    @staticmethod
    def format_breakpoints(break_points: list) -> list:
        return [
            (break_point['w'], break_point['h']) 
                for break_point in break_points
        ]

    @staticmethod
    def rotate_dimensions(rotator, direction):
        """The width and height of a cap relative to a direction, `vertical` or `horizontal`.

        :param cap: _description_
        :type cap: _type_
        :param direction: _description_
        :type direction: _type_
        :return: _description_
        :rtype: _type_
        """
        if rotator['definition'] in ['left', 'right', 'horizontal']:
            if direction =='horizontal':
                return rotator['size']['w'], rotator['size']['h']
            if direction == 'vertical':
                return rotator['size']['h'], rotator['size']['w']
        elif rotator['definition'] in ['up', 'down', 'vertical']:
            if direction == 'horizontal':
                return rotator['size']['h'], rotator['size']['w']
            if direction == 'vertical':
                return rotator['size']['w'], rotator['size']['h']


    def __init__(self, player_device: device.Device, ontology_path: str = settings.DEFAULT_DIR):
        config = conf.Conf(ontology_path).load_interface_configuration()
        state_ao = state.State(ontology_path).get_state('dynamic')
        self.styles = config.get('hud').get('styles')
        self._init_conf(config)
        self._find_media_size(player_device)
        self._init_slot_positions(player_device)
        self._init_slots(state_ao)
        self._init_mirrors(state_ao)


    def _init_conf(self, config: conf.Conf):
        self.styles = config['styles']
        self.hud_conf = config['hud']
        self.sizes = config['sizes']
        self.breakpoints = config['breakpoints']
        self.properties = config['properties']


    def _find_media_size(self, player_device: device.Device):
        breakpoints = self.format_breakpoints(self.breakpoints)
        dim = player_device.dimensions
        for i, break_point in enumerate(breakpoints):
            if dim[0] < break_point[0] and dim[1] < break_point[1]:
                self.media_size = self.sizes[i]
                break
        if self.media_size is None:
            self.media_size = self.sizes[len(self.sizes)-1]


    def _init_mirror_positions(self, player_device: device.Device):
        """_summary_

        :param player_device: _description_
        :type player_device: device.Device

        .. note::
            Remember, just because the position is initalized doesn't mean it will be used. The player could have less life than the number of display positions. However, still need to calculate everything, just in case.
        """
        log.debug('Initializing mirror positions on device...', 
            'HUD._init_mirror_positions')
        mirror_styles = self.styles[self.media_size]['mirrors']

        life_cols = self.properties['mirrors']['life']['columns']
        life_rows = self.properties['mirrors']['life']['rows']
        life_dim = (
            self.hud_conf[self.media_size]['mirrors']['unit']['size']['w'],
            self.hud_conf[self.media_size]['mirrors']['unit']['size']['h']
        )
        x_margins = settings.GUI_MARGINS*player_device.dimensions[0]
        y_margins = settings.GUI_MARGINS*player_device.dimensions[1]

        if mirror_styles['stack'] == 'horizontal':
            if mirror_styles['alignment']['horizontal'] == 'right':
                x_start = player_device.dimensions[0] - \
                    x_margins - \
                    life_rows *life_dim[0]*(1 + MIRROR_PADDING) 

            elif mirror_styles['alignment']['horizontal'] == 'left':
                x_start = x_margins
            else: # center
                x_start = (player_device.dimensions[0] - \
                    life_rows * life_dim[0] *(1 + MIRROR_PADDING))/2

            if mirror_styles['alignment']['vertical'] == 'top':
                y_start = y_margins
            else:
                y_start = player_device.dimensions[1] - \
                    y_margins - \
                    life_cols * life_dim[1] *(1 + MIRROR_PADDING)

        elif mirror_styles['stack'] == 'vertical':
            if mirror_styles['alignment']['horizontal'] == 'right':
                x_start = player_device.dimensions[0] - \
                    x_margins - \
                    life_rows * life_dim[0] * (1 + MIRROR_PADDING)
            elif mirror_styles['alignment']['horizontal'] == 'left':
                x_start = x_margins

            if mirror_styles['alignment']['vertical'] == 'top':
                y_start = y_margins
            elif mirror_styles['alignment']['vertical'] == 'bottom':
                y_start = player_device.dimensions[1] - \
                    y_margins - \
                    life_cols * life_dim[1] * (1 + MIRROR_PADDING)


    def _init_slot_positions(self, player_device: device.Device):
        log.debug('Initializing slot positions on device...', 
            'HUD._init_slot_positions')

        slots_total = self.properties['slots']['total']
        slot_styles = self.styles[self.media_size]['slots']
        x_margins = settings.GUI_MARGINS*player_device.dimensions[0]
        y_margins = settings.GUI_MARGINS*player_device.dimensions[1]

        cap_dim = self.rotate_dimensions(
            self.hud_conf[self.media_size]['slots']['cap'],
            self.styles[self.media_size]['slots']['stack']
        )
        buffer_dim = self.rotate_dimensions(
            self.hud_conf[self.media_size]['slots']['buffer'],
            self.styles[self.media_size]['slots']['stack']
        )
        slot_dim = (
            self.hud_conf[self.media_size]['slots']['empty']['size']['w'],
            self.hud_conf[self.media_size]['slots']['empty']['size']['h']
        )

        if slot_styles['stack'] == 'horizontal':
            buffer_correction = (slot_dim[1] - buffer_dim[1])/2
            cap_correction = (slot_dim[1] - cap_dim[1])/2 

            if slot_styles['alignment']['horizontal'] == 'right':
                x_start = player_device.dimensions[0] \
                    - x_margins \
                    - slots_total*slot_dim[0] \
                    - (slots_total-1)*buffer_dim[0] \
                    - 2*cap_dim[0]
            elif slot_styles['alignment']['horizontal'] == 'left':
                x_start = x_margins
            else: # center
                x_start = (player_device.dimensions[0] \
                    - slots_total*slot_dim[0] \
                    - (slots_total-1)*buffer_dim[0] \
                    - 2*cap_dim[0])/2

            if slot_styles['alignment']['vertical'] == 'top':
                y_start = y_margins
            else:
                y_start = player_device.dimensions[1] \
                    - y_margins \
                    - slot_dim[1]

        elif slot_styles['stack'] == 'vertical':
            buffer_correction = (slot_dim[0] - buffer_dim[0])/2
            cap_correction = (slot_dim[0] - cap_dim[0])/2

            if slot_styles['alignment']['horizontal'] == 'left':
                x_start = x_margins
            else:
                x_start = player_device.dimensions[0] \
                    - x_margins \
                    - slot_dim[0]

            if slot_styles['alignment']['vertical'] == 'bottom':
                y_start = player_device.dimensions[1] \
                    - y_margins \
                    - slots_total*slot_dim[1] \
                    - (slots_total-1)*buffer_dim[1] \
                    - 2*cap_dim[1]
            elif slot_styles['alignment']['vertical'] == 'center':
                y_start = (player_device.dimensions[1] \
                    - slots_total*slot_dim[1] \
                    - (slots_total-1)*buffer_dim[1] \
                    - 2*cap_dim[1])/2
            else: 
                y_start = y_margins

        # number of slots + number of buffer + number of caps
        num = slots_total + (slots_total - 1) + 2
        if slot_styles['stack'] == 'horizontal':
            for i in range(num):
                if i == 0:
                    self.slot_rendering_points.append(
                        (
                            x_start, 
                            y_start + cap_correction
                        )
                    )
                elif i == 1:
                    self.slot_rendering_points.append(
                        (
                            self.slot_rendering_points[i-1][0] + cap_dim[0], 
                            y_start
                        )
                    )
                elif i == num - 1:
                    self.slot_rendering_points.append(
                        (
                            self.slot_rendering_points[i-1][0] + slot_dim[0], 
                            y_start + cap_correction
                        )
                    )
                elif i % 2 == 0:
                    self.slot_rendering_points.append(
                        (
                            self.slot_rendering_points[i-1][0] + slot_dim[0], 
                            y_start + buffer_correction
                        )
                    )
                else:
                    self.slot_rendering_points.append(
                        (
                            self.slot_rendering_points[i-1][0] + buffer_dim[0], 
                            y_start
                        )
                    )

        elif slot_styles['stack'] == 'vertical':
            for i in range(num):
                if i == 0:
                    self.slot_rendering_points.append(
                        (
                            x_start + cap_correction, 
                            y_start
                        )
                    )
                elif i == 1:
                    self.slot_rendering_points.append(
                        (
                            x_start,
                            self.slot_rendering_points[i-1][1] + cap_dim[1]
                        )
                    )
                elif i == num - 1:
                    self.slot_rendering_points.append(
                        (
                            x_start + cap_correction,
                            self.slot_rendering_points[i-1][1] + slot_dim[1]
                        )
                    )
                elif i % 2 == 0:
                    self.slot_rendering_points.append(
                        (
                            x_start + buffer_correction,
                            self.slot_rendering_points[i-1][1] + slot_dim[1]
                        )
                    )
                else:
                    self.slot_rendering_points.append(
                        (
                            x_start,
                            self.slot_rendering_points[i-1][1] + buffer_dim[1]
                        )
                    )


    def _init_slots(self, state_ao):
        self.slots = state_ao['hero']['slots']


    def _init_mirrors(self, state_ao: state.State):
        state_ao['hero']['health']['current'], state_ao['hero']['health']['max']


    def get_cap_directions(self):
        if self.styles[self.media_size]['slots']['stack'] == 'horizontal':
            return ('left', 'right')
        return ('up', 'down')


    def get_buffer_direction(self):
        return self.styles[self.media_size]['slots']['stack']


    def get_buffer_dimensions(self):
        return self.rotate_dimensions(self.hud_conf[self.media_size]['slots']['buffer'])


    def get_cap_dimensions(self):
        return self.rotate_dimensions(self.hud_conf[self.media_size]['slots']['cap'])


    def get_rendering_points(self):
        return self.slot_rendering_points
        

    def get_slot_dimensions(self):
        return (
            self.hud_conf[self.media_size]['slots']['empty']['size']['w'], 
            self.hud_conf[self.media_size]['slots']['empty']['size']['h']
        )


    def slot_frame_map(self):
        return {
            key: 'empty' if val is None else 'equipped' 
            for key, val in self.slots.items()
        }


    def update(self, game_world: world.World):
        self.slots = game_world.hero['slots']


    def toggle(self) -> None:
        self.activated = not self.activated
