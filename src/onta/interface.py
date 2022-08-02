
import onta.settings as settings
import onta.device as device
import onta.world as world
import onta.load.conf as conf
import onta.load.state as state
import onta.util.logger as logger

log = logger.Logger('onta.hud', settings.LOG_LEVEL)

SLOT_STATES = [ 'cast', 'shoot', 'thrust', 'slash' ]
SLOT_PIECES = [ 'cap', 'buffer', 'enabled', 'active', 'disabled']
BUTTON_PIECES = [ 'left', 'middle', 'right' ]
MIRROR_PIECES = [ 'unit', 'empty' ]
SLOT_MARGINS = (0.025, 0.025)
MIRROR_MARGINS = (0.025, 0.025)
MIRROR_PADDING = (0.005, 0.005)
MENU_MARGINS = (0.05, 0.20)
MENU_PADDING = (0.05, 0.05)
PACK_MARGINS = (0.025, 0.025)
MAX_LIFE = 20

def format_breakpoints(break_points: list) -> list:
    return [
        (break_point['w'], break_point['h']) 
            for break_point in break_points
    ]

def rotate_dimensions(rotator: dict, direction: str) -> tuple:
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

def find_media_size(player_device: device.Device, sizes: list, breakpoints: list) -> str:
    dim = player_device.dimensions
    for i, break_point in enumerate(breakpoints):
        if dim[0] < break_point[0] and dim[1] < break_point[1]:
            return sizes[i]
    return sizes[len(sizes)-1]

class HUD():
    hud_conf = {}
    styles = {}
    properties = {}
    slots = {}
    mirrors = {}
    packs = {}
    equipment = {}
    sizes = []
    breakpoints = []
    slot_rendering_points = []
    life_rendering_points = []
    pack_rendering_points = []
    hud_activated = True
    media_size = None


    def __init__(
        self, 
        player_device: device.Device, 
        ontology_path: str = settings.DEFAULT_DIR
    ) -> None:
        config = conf.Conf(ontology_path).load_interface_configuration()
        state_ao = state.State(ontology_path).get_state('dynamic')
        self.styles = config.get('hud').get('styles')
        self._init_conf(config)
        self.media_size = find_media_size(
            player_device, 
            self.sizes, 
            self.breakpoints
        )
        self._init_slot_positions(player_device)
        self._init_mirror_positions(player_device)
        self._init_pack_positions(player_device)
        self._init_slots(state_ao)
        self._init_mirrors(state_ao)
        self._init_packs(state_ao)
        self._init_equipment(state_ao)


    def _init_conf(self, config: conf.Conf) -> None:
        self.styles = config['styles']
        self.hud_conf = config['hud']
        self.sizes = config['sizes']
        self.breakpoints = format_breakpoints(config['breakpoints'])
        self.properties = config['properties']


    def _init_pack_positions(self, player_device: device.Device):
        pack_styles = self.styles[self.media_size]['packs']

        x_margins = PACK_MARGINS[0]*player_device.dimensions[0]
        y_margins = PACK_MARGINS[1]*player_device.dimensions[1]

        packset = self.hud_conf[self.media_size]['packs']

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
        # NOTE: dependent on 'unit' and 'empty' being the same dimensions...
        life_dim = (
            self.hud_conf[self.media_size]['mirrors']['life']['unit']['size']['w'],
            self.hud_conf[self.media_size]['mirrors']['life']['unit']['size']['h']
        )
        x_margins = MIRROR_MARGINS[0]*player_device.dimensions[0]
        y_margins = MIRROR_MARGINS[1]*player_device.dimensions[1]

        if mirror_styles['alignment']['horizontal'] == 'right':
            x_start = player_device.dimensions[0] - \
                x_margins - \
                life_cols * life_dim[0]*(1 + MIRROR_PADDING[0]) 

        elif mirror_styles['alignment']['horizontal'] == 'left':
            x_start = x_margins
        else: # center
            x_start = (player_device.dimensions[0] - \
                life_cols * life_dim[0] *(1 + MIRROR_PADDING[0]))/2
        
        if mirror_styles['alignment']['vertical'] == 'top':
            y_start = y_margins
        elif mirror_styles['alignment']['vertical'] == 'bottom':
            y_start = player_device.dimensions[1] - \
                y_margins - \
                life_rows * life_dim[1] * (1 + MIRROR_PADDING[1])
        else: # center
            y_start = (player_device.dimensions[1] - \
                life_rows * life_dim[1] * (1 + MIRROR_PADDING[1]))/2


        if mirror_styles['stack'] == 'vertical':
            (life_rows, life_cols) = (life_cols, life_rows)
            
        for row in range(life_rows):
            for col in range(life_cols):

                if (row+1)*col == 0:
                    self.life_rendering_points.append(
                        (
                            x_start, 
                            y_start
                        )
                    )
                else:
                    if mirror_styles['stack'] == 'horizontal':
                        self.life_rendering_points.append(
                            (
                                self.life_rendering_points[(row+1)*col - 1][0] + \
                                    life_dim[0]*(1+MIRROR_PADDING[0]),
                                self.life_rendering_points[(row+1)*col - 1][1]
                            )
                        )
                    else:
                        self.life_rendering_points.append(
                            (
                                self.life_rendering_points[(row+1)*col - 1][0] + \
                                    life_dim[0],
                                self.life_rendering_points[(row+1)*col - 1][1] + \
                                    life_dim[1]*(1+MIRROR_PADDING[1])
                            )
                        )

        self.life_rendering_points.reverse()
            

    def _init_slot_positions(self, player_device: device.Device):
        log.debug('Initializing slot positions on device...', 
            'HUD._init_slot_positions')

        slots_total = self.properties['slots']['total']
        slot_styles = self.styles[self.media_size]['slots']
        x_margins = SLOT_MARGINS[0]*player_device.dimensions[0]
        y_margins = SLOT_MARGINS[1]*player_device.dimensions[1]

        cap_dim = rotate_dimensions(
            self.hud_conf[self.media_size]['slots']['cap'],
            self.styles[self.media_size]['slots']['stack']
        )
        buffer_dim = rotate_dimensions(
            self.hud_conf[self.media_size]['slots']['buffer'],
            self.styles[self.media_size]['slots']['stack']
        )
        # NOTE: dependent on 'empty' and 'equipped' being the same dimensions...
        slot_dim = (
            self.hud_conf[self.media_size]['slots']['empty']['size']['w'],
            self.hud_conf[self.media_size]['slots']['empty']['size']['h']
        )

        if slot_styles['alignment']['horizontal'] == 'right':
            x_start = player_device.dimensions[0] \
                - x_margins \
                - slots_total*slot_dim[0] \
                - (slots_total-1)*buffer_dim[0] \
                - 2*cap_dim[0]
        elif slot_styles['alignment']['horizontal'] == 'center':
            x_start = (player_device.dimensions[0] \
                - slots_total*slot_dim[0] \
                - (slots_total-1)*buffer_dim[0] \
                - 2*cap_dim[0])/2
                
        else: # left
            x_start = x_margins

                
        if slot_styles['alignment']['vertical'] == 'bottom':
            if slot_styles['stack'] == 'horizontal':
                y_start = player_device.dimensions[1] \
                    - y_margins \
                    - slot_dim[1] 
            elif slot_styles['stack'] == 'vertical':
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
        else: # top
            y_start = y_margins

        # number of slots + number of buffers + number of caps
        num = slots_total + (slots_total - 1) + 2
        if slot_styles['stack'] == 'horizontal':
            buffer_correction = (slot_dim[1] - buffer_dim[1])/2
            cap_correction = (slot_dim[1] - cap_dim[1])/2 

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
            buffer_correction = (slot_dim[0] - buffer_dim[0])/2
            cap_correction = (slot_dim[0] - cap_dim[0])/2
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

    
    def _init_slots(self, state_ao: state.State):
        self.slots = state_ao['hero']['slots']


    def _init_equipment(self, state_ao: state.State):
        self.equipment = state_ao['hero']['equipment']


    def _init_packs(self, state_ao: state.State): 
        pass


    def _init_mirrors(self, state_ao: state.State):
        self.mirrors = {
            'life': state_ao['hero']['health']
        }
        

    def get_cap_directions(self):
        if self.styles[self.media_size]['slots']['stack'] == 'horizontal':
            return ('left', 'right')
        return ('up', 'down')


    def get_buffer_direction(self):
        return self.styles[self.media_size]['slots']['stack']


    def get_buffer_dimensions(self):
        return rotate_dimensions(self.hud_conf[self.media_size]['slots']['buffer'])


    def get_cap_dimensions(self):
        return rotate_dimensions(self.hud_conf[self.media_size]['slots']['cap'])


    def get_rendering_points(self, interface_key):
        if interface_key in ['slot', 'slots']:
            return self.slot_rendering_points
        elif interface_key in ['mirror', 'mirrors']:
            return self.life_rendering_points    


    def get_slot_dimensions(self):
        return (
            self.hud_conf[self.media_size]['slots']['empty']['size']['w'], 
            self.hud_conf[self.media_size]['slots']['empty']['size']['h']
        )


    def slot_frame_map(self):
        # TODO: need to calculate disabled slots from hero state
        return {
            key: 'enabled' if val is None else 'active' 
            for key, val in self.slots.items()
        }


    def life_frame_map(self):
        return {
            i: 'unit' if i <= self.mirrors['life']['current'] - 1 else 'empty'
            for i in range(MAX_LIFE)
            if i <= self.mirrors['life']['max'] - 1
        }


    def update(self, game_world: world.World):
        self.slots = game_world.hero['slots']
        self.equipment = game_world.hero['equipment']
        self.mirrors = {
            'life': game_world.hero['health']
        }


    def toggle_hud(self) -> None:
        self.hud_activated = not self.hud_activated


class Menu():
    menu_conf = {}
    buttons = {}
    menus = {}
    properties = {}
    styles = {}
    sizes = []
    breakpoints = []
    button_rendering_points = []
    menu_activated = False
    active_button = None
    media_size = None


    def __init__(
        self, 
        player_device: device.Device, 
        ontology_path: str = settings.DEFAULT_DIR
    ) -> None:
        config = conf.Conf(ontology_path).load_interface_configuration()
        state_ao = state.State(ontology_path).get_state('dynamic')
        self._init_conf(config)
        self.media_size = find_media_size(
            player_device, 
            self.sizes, 
            self.breakpoints
        )
        self._init_menu_positions(player_device)
        self._init_buttons(state_ao)


    def _init_conf(self, config: conf.Conf) -> None:
        self.menu_conf = config['menu']
        self.sizes = config['sizes']
        self.breakpoints = format_breakpoints(config['breakpoints'])
        self.properties = config['properties']['menu']
        self.styles = config['styles']


    def _init_menu_positions(self, player_device: device.Device) -> None:
        menu_styles = self.styles[self.media_size]['menu']

        # all button component pieces have the same pieces, so any will do...
        button_conf = self.menu_conf[self.media_size]['button']['enabled']

        # [ (left_w, left_h), (middle_w, middle_h), (right_w, right_h) ]
        dims = [
            (
                button_conf[piece]['size']['w'],
                button_conf[piece]['size']['h']
            ) for piece in BUTTON_PIECES
        ]

        full_width = 0
        for dim in dims:
            full_width += dim[0]


        # self.button_rendering_points => len() == len(buttons)*len(pieces)
        # for (0, equipment), (1, inventory), (2, status), ...
        for i in range(len(self.properties['buttons'])):

            # for (0, left), (1, middle), (2, right)
            # j gives you index for the piece dim in dims
            for j in range(len(button_conf)):

                if menu_styles['stack'] == 'vertical':
                    if i == 0 and j == 0:
                        x = (1 - MENU_MARGINS[0])*player_device.dimensions[0] - full_width
                        y = MENU_MARGINS[1]*player_device.dimensions[1]
                    else:
                        if j == 0:
                            x = self.button_rendering_points[0][0]
                            y = self.button_rendering_points[0][1] + \
                                (1+MENU_PADDING[1])*i*dims[0][1]
                        else:
                            x = self.button_rendering_points[j-1][0] + \
                                dims[j-1][0]
                            y = self.button_rendering_points[j-1][1] + \
                                (1+MENU_PADDING[1])*i*dims[j-1][1]

                elif menu_styles['stack'] == 'horizontal':
                    if i == 0 and j == 0:
                        x = MENU_MARGINS[0]*player_device.dimensions[0]
                        y = MENU_MARGINS[1]*player_device.dimensions[1]
                    else:
                        if j == 0 :
                            x = self.button_rendering_points[0][0] + \
                                i*(full_width + MENU_PADDING[0])
                            y = self.button_rendering_points[0][1]
                        else:
                            x = self.button_rendering_points[len(self.button_rendering_points)-1][0] + dims[j-1][0]
                            y = self.button_rendering_points[j-1][1]
            
                self.button_rendering_points.append((x,y))


    def _init_buttons(self, state_ao: state.State) -> dict:
        # TODO: calculate based on state information

        for i, name in enumerate(self.properties['buttons']):
            if i == 0:
                self._activate_button(name)
                self.active_button = i
            else:
                self._enable_button(name)


    def _activate_button(self, button_key):
        self.buttons[button_key] = {
            piece: 'active' for piece in BUTTON_PIECES
        }


    def _disable_button(self, button_key):
        self.buttons[button_key] = {
            piece: 'disabled' for piece in BUTTON_PIECES
        }


    def _enable_button(self, button_key):
        self.buttons[button_key] = {
            piece: 'enabled' for piece in BUTTON_PIECES
        }


    def increment_active_button(self):
        ## TODO: skip disabled buttons
        previous_active = self.active_button
        self.active_button -= 1

        if self.active_button < 0:
            self.active_button = len(self.properties['buttons']) - 1
        
        self._enable_button(self.properties['buttons'][previous_active])
        self._activate_button(self.properties['buttons'][self.active_button])


    def decrement_active_button(self):
        ## TODO: skip disabled buttons
        previous_active = self.active_button
        self.active_button += 1

        if self.active_button > len(self.properties['buttons']) - 1:
            self.active_button = 0
        
        self._enable_button(self.properties['buttons'][previous_active])
        self._activate_button(self.properties['buttons'][self.active_button])


    def button_frame_map(self) -> list:
        frame_map = []
        for piece_conf in self.buttons.values():
            for piece_state in piece_conf.values():
                frame_map.append(piece_state)
        return frame_map


    def button_piece_map(self) -> list:
        piece_map = []
        for piece_conf in self.buttons.values():
            for piece_key in piece_conf.keys():
                piece_map.append(piece_key)
        return piece_map


    def button_maps(self) -> tuple:
        return (self.button_frame_map(), self.button_piece_map())


    def toggle_menu(self) -> None:
        self.menu_activated = not self.menu_activated


    def get_rendering_points(self, interface_key) -> list:
        if interface_key in [ 'button', 'buttons' ]:
            return self.button_rendering_points

    def update(self, user_input):
        if user_input['n']:
            self.increment_active_button()
        elif user_input['s']:
            self.decrement_active_button()