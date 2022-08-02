
from typing import Union
import onta.settings as settings
import onta.device as device
import onta.world as world
import onta.load.conf as conf
import onta.load.state as state
import onta.util.logger as logger

log = logger.Logger('onta.hud', settings.LOG_LEVEL)

# TODO: configuration and styles candidates
SLOT_STATES = [ 'cast', 'shoot', 'thrust', 'slash' ]
SLOT_PIECES = [ 'cap', 'buffer', 'enabled', 'active', 'disabled']
MIRROR_PIECES = [ 'unit', 'empty' ]
SLOT_MARGINS = (0.025, 0.025)
MIRROR_MARGINS = (0.025, 0.025)
MIRROR_PADDING = (0.005, 0.005)
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
    bag_rendering_points = []
    wallet_rendering_points = []
    belt_rendering_points = []
    hud_activated = True
    media_size = None


    def __init__(
        self, 
        player_device: device.Device, 
        ontology_path: str = settings.DEFAULT_DIR
    ) -> None:
        config = conf.Conf(ontology_path)
        state_ao = state.State(ontology_path)
        self._init_conf(config, player_device)
        self._init_slot_positions(player_device)
        self._init_mirror_positions(player_device)
        self._init_pack_positions(player_device)
        self._init_slots(state_ao)
        self._init_mirrors(state_ao)
        self._init_packs(state_ao)
        self._init_equipment(state_ao)


    def _init_conf(self, config: conf.Conf, player_device: device.Device) -> None:
        """Parse and store configuration from yaml files in instance fields.

        :param config: _description_
        :type config: conf.Conf
        :param player_device: _description_
        :type player_device: device.Device
        """
        config = config.load_sense_configuration()
        self.styles = config['styles']
        self.hud_conf = config['hud']
        self.sizes = config['sizes']
        self.breakpoints = format_breakpoints(config['breakpoints'])
        self.properties = config['properties']
        self.media_size = find_media_size(
            player_device, 
            self.sizes, 
            self.breakpoints
        )


    def _init_pack_positions(self, player_device: device.Device):
        """_summary_

        :param player_device: _description_
        :type player_device: device.Device

        .. note::
            The necessity of open source assets imposes some obscurity on the proceedings. Essentially, each type of pack is composed of different pieces and is defined differently in the asset sheet, i.e. each pack type needs treated slightly differently when constructing its rendering position. See documentation for more information.
        """
        pack_margins = (
            self.styles[self.media_size]['packs']['margins']['w'], 
            self.styles[self.media_size]['packs']['margins']['h']
        )
        pack_horizontal_align = self.styles[self.media_size]['packs']['alignment']['horizontal']
        pack_vertical_align = self.styles[self.media_size]['packs']['alignment']['vertical']

        bagset = self.hud_conf[self.media_size]['packs']['bag']

        total_bag_width = 0
        for bag_piece in bagset.values():
            total_bag_width += bag_piece['size']['w']

        # dependent on both pieces being the same height
        # i.e., the pack sheet can only be broken in the 
        # horizontal direction
        total_bag_height = bagset[list(bagset.keys())[0]]['size']['h']

        # (0, left), (1, right)
        for i, bag_piece in enumerate(bagset.values()):
            if i == 0:
                if pack_horizontal_align == 'left':
                    x = pack_margins[0]*player_device.dimensions[0]
                elif pack_horizontal_align == 'right':
                    x = (1-pack_margins[0])*player_device.dimensions[0] - \
                        total_bag_width

                if pack_vertical_align == 'top':
                    y = pack_margins[1]*player_device.dimensions[1]
                elif pack_vertical_align == 'bottom':
                    y = (1-pack_margins[0])*player_device.dimensions[1] - \
                        total_bag_height
            else:
                x = self.bag_rendering_points[i-1][0] + prev_w
                y = self.bag_rendering_points[i-1][1]
            self.bag_rendering_points.append((x,y))
            prev_w = bag_piece['size']['w']

        beltset = self.hud_conf[self.media_size]['packs']['belt']

        total_belt_width = 0
        for belt_piece in beltset.values():
            total_belt_width += belt_piece['size']['w']
        total_belt_height = beltset[list(beltset.keys())[0]]['size']['h']

        # belt initial position only affected by pack vertical alignment
        for i, belt_piece in enumerate(beltset.values()):
            if i == 0:
                if pack_horizontal_align == 'left':
                    # dependent on bag height > belt height
                    x = self.bag_rendering_points[0][0] + \
                            (1+pack_margins[0])*total_bag_width
                    y = self.bag_rendering_points[0][1] + \
                            (total_bag_height-total_belt_height)/2
                elif pack_horizontal_align == 'right':
                    x = self.bag_rendering_points[0][0] - \
                            (1+pack_margins[0])*total_bag_width
                    y = self.bag_rendering_points[0][1] + \
                            (total_bag_height-total_belt_height)/2  
            else:
                x = self.belt_rendering_points[i-1][0] + prev_w
                y = self.belt_rendering_points[i-1][1]
            self.belt_rendering_points.append((x,y))
            prev_w = belt_piece['size']['w']
        
            

        wallet = self.hud_conf[self.media_size]['packs']['wallet']['display']
        wallet_w, wallet_h = wallet['size']['w'], wallet['size']['h']

        if pack_horizontal_align == 'left':
            self.wallet_rendering_points.append(
                (
                    self.belt_rendering_points[0][0] + \
                        (1 + pack_margins[0])*total_belt_width,
                    self.bag_rendering_points[0][1] +
                        (total_belt_height - wallet_h * (2 + pack_margins[1]))/2
                )
            )
        elif pack_horizontal_align == 'right':
            self.wallet_rendering_points.append(
                (
                    self.bag_rendering_points[0][0] - \
                        (1 + pack_margins[0])*total_belt_width - \
                        wallet_w,
                    self.bag_rendering_points[0][1] + \
                        (total_belt_height - wallet_h * (2 + pack_margins[1]))/2
                )
            )
        self.wallet_rendering_points.append(
            (
                self.wallet_rendering_points[0][0],
                self.wallet_rendering_points[0][1] + \
                    (1+pack_margins[1])*wallet_h
            )
        )

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
            self.hud_conf[self.media_size]['slots']['disabled']['size']['w'],
            self.hud_conf[self.media_size]['slots']['disabled']['size']['h']
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
        dynamic_state = state_ao.get_state('dynamic')
        self.slots = dynamic_state['hero']['slots']


    def _init_equipment(self, state_ao: state.State):
        dynamic_state = state_ao.get_state('dynamic')
        self.equipment = dynamic_state['hero']['equipment']


    def _init_packs(self, state_ao: state.State): 
        dynamic_state = state_ao.get_state('dynamic')


    def _init_mirrors(self, state_ao: state.State):
        dynamic_state = state_ao.get_state('dynamic')
        self.mirrors = {
            'life': dynamic_state['hero']['health']
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


    def get_rendering_points(self, interface_key: str) -> Union[list, tuple]:
        if interface_key in ['slot', 'slots']:
            return self.slot_rendering_points
        elif interface_key in ['life', 'lives']:
            return self.life_rendering_points    
        elif interface_key in ['bag', 'bags']:
            return self.bag_rendering_points
        elif interface_key in ['wallet', 'wallets']:
            return self.wallet_rendering_points
        elif interface_key in ['belt','belts']:
            return self.belt_rendering_points


    def get_slot_dimensions(self) -> tuple:
        return (
            self.hud_conf[self.media_size]['slots']['disabled']['size']['w'], 
            self.hud_conf[self.media_size]['slots']['disabled']['size']['h']
        )


    def slot_frame_map(self) -> dict:
        # TODO: need to calculate disabled slots from hero state
        # TODO: should parameterize key somehow
        return {
            key: 'enabled' if val is None else 'active' 
            for key, val in self.slots.items()
        }


    def mirror_frame_map(self, mirror_key: str) -> dict:
        # TODO: need to calculate disabled slots from hero state
        # TODO: should parameterize the key somehow
        if mirror_key == 'life':
            return {
                i: 'unit' if i <= self.mirrors['life']['current'] - 1 else 'empty'
                for i in range(MAX_LIFE)
                if i <= self.mirrors['life']['max'] - 1
            }


    def pack_frame_map(self, pack_key: str) -> dict:
        packset = self.hud_conf[self.media_size]['packs'][pack_key]
        if pack_key in ['bag', 'bags', 'belt', 'belts']:
            return {
                i: key for i, key in enumerate(packset)
            }
        elif pack_key == 'wallet':
            return {
                0: 'display',
                1: 'display'
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
    tabs = {}
    properties = {}
    styles = {}
    sizes = []
    breakpoints = []
    button_rendering_points = []
    menu_activated = False
    active_button = None
    active_tab = None
    media_size = None


    def __init__(
        self, 
        player_device: device.Device, 
        ontology_path: str = settings.DEFAULT_DIR
    ) -> None:
        config = conf.Conf(ontology_path).load_sense_configuration()
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
        self.styles = config['styles']
        self.properties = config['properties']['menu']
        self.breakpoints = format_breakpoints(config['breakpoints'])
        self.tabs = {
            button_name: {} 
            for button_name in self.properties['button']['buttons']
        }


    def _init_menu_positions(self, player_device: device.Device) -> None:
        menu_margins = (
            self.styles[self.media_size]['menu']['margins']['w'],
            self.styles[self.media_size]['menu']['margins']['h']
        )
        menu_padding = (
            self.styles[self.media_size]['menu']['padding']['w'],
            self.styles[self.media_size]['menu']['padding']['h']
        )
        menu_stack = self.styles[self.media_size]['menu']['stack']
        # all button component pieces have the same pieces, so any will do...
        button_conf = self.menu_conf[self.media_size]['button']['enabled']

        # [ (left_w, left_h), (middle_w, middle_h), (right_w, right_h) ]
        dims = [
            (
                button_conf[piece]['size']['w'],
                button_conf[piece]['size']['h']
            ) for piece in self.properties['button']['pieces']
        ]

        full_width = 0
        for dim in dims:
            full_width += dim[0]


        # self.button_rendering_points => len() == len(buttons)*len(pieces)
        # for (0, equipment), (1, inventory), (2, status), ...
        for i in range(len(self.properties['button']['buttons'])):

            # for (0, left), (1, middle), (2, right)
            # j gives you index for the piece dim in dims
            for j in range(len(button_conf)):

                if menu_stack == 'vertical':
                    if i == 0 and j == 0:
                        x = (1 - menu_margins[0])*player_device.dimensions[0] - full_width
                        y = menu_margins[1]*player_device.dimensions[1]
                    else:
                        if j == 0:
                            x = self.button_rendering_points[0][0]
                            y = self.button_rendering_points[0][1] + \
                                (1+menu_padding[1])*i*dims[0][1]
                        else:
                            x = self.button_rendering_points[j-1][0] + \
                                dims[j-1][0]
                            y = self.button_rendering_points[j-1][1] + \
                                (1+menu_padding[1])*i*dims[j-1][1]

                elif menu_stack == 'horizontal':
                    if i == 0 and j == 0:
                        x = menu_margins[0]*player_device.dimensions[0]
                        y = menu_margins[1]*player_device.dimensions[1]
                    else:
                        if j == 0 :
                            x = self.button_rendering_points[0][0] + \
                                i*(full_width + menu_padding[0])
                            y = self.button_rendering_points[0][1]
                        else:
                            x = self.button_rendering_points[len(self.button_rendering_points)-1][0] + dims[j-1][0]
                            y = self.button_rendering_points[j-1][1]
            
                self.button_rendering_points.append((x,y))


    def _init_buttons(self, state_ao: state.State) -> dict:
        # TODO: calculate based on state information

        for i, name in enumerate(self.properties['button']['buttons']):
            if i == 0:
                self._activate_button(name)
                self.active_button = i
            else:
                self._enable_button(name)


    def _activate_button(self, button_key):
        self.buttons[button_key] = {
            piece: 'active' for piece in self.properties['button']['pieces']
        }


    def _disable_button(self, button_key):
        self.buttons[button_key] = {
            piece: 'disabled' for piece in self.properties['button']['pieces']
        }


    def _enable_button(self, button_key):
        self.buttons[button_key] = {
            piece: 'enabled' for piece in self.properties['button']['pieces']
        }


    def _increment_active_button(self):
        ## TODO: skip disabled buttons
        previous_active = self.active_button
        self.active_button -= 1

        if self.active_button < 0:
            self.active_button = len(self.properties['button']['buttons']) - 1
        
        self._enable_button(self.properties['button']['buttons'][previous_active])
        self._activate_button(self.properties['button']['buttons'][self.active_button])


    def _decrement_active_button(self):
        ## TODO: skip disabled buttons
        previous_active = self.active_button
        self.active_button += 1

        if self.active_button > len(self.properties['button']['buttons']) - 1:
            self.active_button = 0
        
        self._enable_button(self.properties['button']['buttons'][previous_active])
        self._activate_button(self.properties['button']['buttons'][self.active_button])


    def execute_active_button(self):
        pass


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
            self._increment_active_button()
        elif user_input['s']:
            self._decrement_active_button()