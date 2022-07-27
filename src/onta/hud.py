
import onta.settings as settings
import onta.device as device
import onta.world as world
import onta.load.conf as conf
import onta.load.state as state
import onta.util.logger as logger

log = logger.Logger('onta.hud', settings.LOG_LEVEL)

SLOTS_TOTAL = 4
SLOT_STATES = [ 'cast', 'shoot', 'thrust', 'slash' ]

class HUD():

    # HUD will essentially be its own world. let view decide how it is rendered.

    hud_conf = None
    activated = True
    media_size = None
    styles = None
    sizes = None
    breakpoints = None
    slots = None
    rendering_points = None

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
        if self.media_size is None:
            self.media_size = self.sizes[len(self.sizes)-1]


    def _init_positions(self, player_device:device.Device):
         # note the difference between the 'slots' key in the hud_conf dict 
        # and the self.slots property. the first represents image configuration properties
        # the second represents player state information

        # if stacking horizontal to the right, 
        #   if cap definition is left or right:
        #       cap_width = width
        #   if cap definition is up or down:
        #       cap_width = height
        slots_total = SLOTS_TOTAL
        slot_styles = self.styles[self.media_size]['slots']
        x_margins = settings.SLOT_MARGINS*player_device.dimensions[0]
        y_margins = settings.SLOT_MARGINS*player_device.dimensions[1]

        cap_dim = self.rotate_dimensions(
            self.hud_conf[self.media_size]['slots']['cap']['image'],
            self.styles[self.media_size]['slots']['stack']
        )
        buffer_dim = self.rotate_dimensions(
            self.hud_conf[self.media_size]['slots']['buffer']['image'],
            self.styles[self.media_size]['slots']['stack']
        )
        slot_dim = (
            self.hud_conf[self.media_size]['slots']['empty']['image']['size']['w'],
            self.hud_conf[self.media_size]['slots']['empty']['image']['size']['h']
        )

        log.debug('Initializing interface screen positions...', 
            'HUD._init_positions')

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


        self.rendering_points = []
        # number of slots + number of buffer + number of caps
        num = slots_total + (slots_total - 1) + 2
        if slot_styles['stack'] == 'horizontal':
            for i in range(num):
                if i == 0:
                    self.rendering_points.append(
                        (
                            x_start, 
                            y_start + cap_correction
                        )
                    )
                elif i == num - 1:
                    self.rendering_points.append(
                        (
                            self.rendering_points[i-1][0] + slot_dim[0], 
                            y_start + cap_correction
                        )
                    )
                elif i % 2 == 0:
                    self.rendering_points.append(
                        (
                            self.rendering_points[i-1][0] + slot_dim[0], 
                            y_start + buffer_correction
                        )
                    )
                elif i % 2 == 1:
                    if i == 1:
                        self.rendering_points.append(
                            (
                                self.rendering_points[i-1][0] + cap_dim[0], 
                                y_start
                            )
                        )
                    else:
                        self.rendering_points.append(
                            (
                                self.rendering_points[i-1][0] + buffer_dim[0], 
                                y_start
                            )
                        )

        elif slot_styles['stack'] == 'vertical':
            for i in range(num):
                if i == 0:
                    self.rendering_points.append(
                        (
                            x_start + cap_correction, 
                            y_start
                        )
                    )
                elif i == num - 1:
                    self.rendering_points.append(
                        (
                            x_start + cap_correction,
                            self.rendering_points[i-1][1] + slot_dim[1]
                        )
                    )
                elif i % 2 == 0:
                    self.rendering_points.append(
                        (
                            x_start + buffer_correction,
                            self.rendering_points[i-1][1] + slot_dim[1]
                        )
                    )
                elif i % 2 == 1:
                    if i == 1:
                        self.rendering_points.append(
                            (
                                x_start,
                                self.rendering_points[i-1][1] + cap_dim[1]
                            )
                        )
                    else:
                        self.rendering_points.append(
                            (
                                x_start,
                                self.rendering_points[i-1][1] + buffer_dim[1]
                            )
                        )

    def _init_slots(self, state_ao):
        self.slots = state_ao.get('hero').get('slots')


    def _init_mirrors(self, state_ao: state.State):
        pass


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
        return self.rendering_points
        

    def get_slot_dimensions(self):
        return (
            self.hud_conf[self.media_size]['slots']['empty']['image']['size']['w'], 
            self.hud_conf[self.media_size]['slots']['empty']['image']['size']['h']
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
