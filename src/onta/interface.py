
from typing import Union
import onta.settings as settings
import onta.device as device
import onta.world as world
import onta.load.conf as conf
import onta.load.state as state
import onta.util.logger as logger

log = logger.Logger('onta.hud', settings.LOG_LEVEL)

PACK_TYPES = [ 'bag', 'belt', 'wallet' ]
MIRROR_TYPES = [ 'life', 'magic' ]

def format_breakpoints(
    break_points: list
) -> list:
    """_summary_

    :param break_points: _description_
    :type break_points: list
    :return: _description_
    :rtype: list
    """
    return [
        (break_point['w'], break_point['h']) 
            for break_point in break_points
    ]

def rotate_dimensions(
    rotator: dict, 
    direction: str
) -> tuple:
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
            return (
                rotator['size']['w'], 
                rotator['size']['h']
            )
        if direction == 'vertical':
            return (
                rotator['size']['h'], 
                rotator['size']['w']
            )
    elif rotator['definition'] in ['up', 'down', 'vertical']:
        if direction == 'horizontal':
            return (
                rotator['size']['h'], 
                rotator['size']['w']
            )
        if direction == 'vertical':
            return (
                rotator['size']['w'], 
                rotator['size']['h']
            )

def find_media_size(
    player_device: device.Device, 
    sizes: list, 
    breakpoints: list
) -> str:
    """_summary_

    :param player_device: _description_
    :type player_device: device.Device
    :param sizes: _description_
    :type sizes: list
    :param breakpoints: _description_
    :type breakpoints: list
    :return: _description_
    :rtype: str
    """
    dim = player_device.dimensions
    for i, break_point in enumerate(breakpoints):
        if dim[0] < break_point[0] and dim[1] < break_point[1]:
            return sizes[i]
    return sizes[len(sizes)-1]

class HUD():
    """
    ```python
    ```
    """

    hud_conf = {}
    """
    ```python
    ```
    """
    avatar_conf = {}
    # NOTE: not sure if its the best idea storing this in HUD, the information
    #       implicitly exists in repo already, but then would need a reference
    #       to repo in HUD, so...this seems to be the ideal solution.
    """
    ```python
    ```
    """
    styles = {}
    """
    ```python
    ```
    """
    properties = {}
    """
    ```python
    ```
    """
    slots = {}
    """
    ```python
    ```
    """
    mirrors = {}
    """
    ```python
    ```
    """
    packs = {}
    """
    ```python
    ```
    """
    equipment = {}
    """
    ```python
    ```
    """
    sizes = []
    """
    ```python
    ```
    """
    breakpoints = []
    """
    ```python
    ```
    """
    slot_rendering_points = []
    """
    ```python
    ```
    """
    life_rendering_points = []
    """
    ```python
    ```
    """
    bag_rendering_points = []
    """
    ```python
    ```
    """
    wallet_rendering_points = []
    """
    ```python
    ```
    """
    belt_rendering_points = []
    """
    ```python
    ```
    """
    avatar_rendering_points = []
    """
    ```python
    self.avatar_rendering_points = [
        slot_1_avatar_pt, # tuple
        slot_2_avatar_pt, # tuple
        slot_3_avatar_pt, # tuple,
        slot_4_avatar_pt, # tuple
        bag_avatar_pt, # tuple
        belt_avatar_pt, # tuple
        wallet_coin_avatar_pt, # tuple
        wallet_key_avatar_pt, # tuple
    ]
    ```
    """
    avatar_frame_map = {}
    pack_frame_map = {}
    slot_frame_map = {}
    life_frame_map = {}
    belt_frame_map = {}
    bag_frame_map = {}
    wallet_frame_map = {}

    # NOTE: need to separate maps from rendering points since rendering points don't change, but maps do.
    #       easier to maintain this way?
    hud_activated = True
    """
    ```python
    ```
    """
    media_size = None
    """
    ```python
    ```
    """


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
        self._init_internal_state(state_ao)
        self._calculate_avatar_positions()


    def _init_conf(
        self, 
        config: conf.Conf, 
        player_device: device.Device
    ) -> None:
        """Parse and store configuration from yaml files in instance fields.

        :param config: _description_
        :type config: conf.Conf
        :param player_device: _description_
        :type player_device: device.Device
        """
        sense_config = config.load_sense_configuration()

        self.styles = sense_config['styles']
        self.hud_conf = sense_config['hud']
        self.sizes = sense_config['sizes']
        self.breakpoints = format_breakpoints(
            sense_config['breakpoints']
        )
        self.properties = sense_config['properties']
        self.media_size = find_media_size(
            player_device, 
            self.sizes, 
            self.breakpoints
        )

        self.avatar_conf = config.load_avatar_configuration()['avatars']


    def _init_pack_positions(
        self, 
        player_device: device.Device
    ) -> None:
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
        wallet_w, wallet_h = (
            wallet['size']['w'], 
            wallet['size']['h']
        )

        if pack_horizontal_align == 'left':
            self.wallet_rendering_points.append(
                (
                    self.belt_rendering_points[0][0] + \
                        (total_belt_width + pack_margins[0]*(total_bag_width+total_belt_width)),
                    self.bag_rendering_points[0][1] + \
                        (total_belt_height - wallet_h * (2 + pack_margins[1]) )/2
                )
            )
        elif pack_horizontal_align == 'right':
            self.wallet_rendering_points.append(
                (
                    self.bag_rendering_points[0][0] - \
                        (total_belt_width + pack_margins[0]*(total_bag_width+total_belt_width)) - \
                        wallet_w,
                    self.bag_rendering_points[0][1] + \
                        (total_belt_height - wallet_h * (2 + pack_margins[1]) )/2
                )
            )
        self.wallet_rendering_points.append(
            (
                self.wallet_rendering_points[0][0],
                self.wallet_rendering_points[0][1] + \
                    (1+pack_margins[1])*wallet_h
            )
        )


    def _init_mirror_positions(
        self, 
        player_device: device.Device
    ) -> None:
        """_summary_

        :param player_device: _description_
        :type player_device: device.Device

        .. note::
            Remember, just because the position is initalized doesn't mean it will be used. The player could have less life than the number of display positions. However, still need to calculate everything, just in case.
        """
        log.debug('Initializing mirror positions on device...', 
            'HUD._init_mirror_positions')
        mirror_styles = self.styles[self.media_size]['mirrors']
        life_rank = (
            self.properties['mirrors']['life']['columns'],
            self.properties['mirrors']['life']['rows'],
        )
        # NOTE: dependent on 'unit' and 'empty' being the same dimensions...
        life_dim = (
            self.hud_conf[self.media_size]['mirrors']['life']['unit']['size']['w'],
            self.hud_conf[self.media_size]['mirrors']['life']['unit']['size']['h']
        )
        margins= (
            mirror_styles['margins']['w']*player_device.dimensions[0],
            mirror_styles['margins']['h']*player_device.dimensions[1]
        )

        if mirror_styles['alignment']['horizontal'] == 'right':
            x_start = player_device.dimensions[0] - \
                margins[0] - \
                life_rank[0] * life_dim[0]*(1 + mirror_styles['padding']['w']) 
        elif mirror_styles['alignment']['horizontal'] == 'left':
            x_start = margins[0]
        else: # center
            x_start = (player_device.dimensions[0] - \
                life_rank[0] * life_dim[0] *(1 + mirror_styles['padding']['w']))/2
        
        if mirror_styles['alignment']['vertical'] == 'top':
            y_start = margins[1]
        elif mirror_styles['alignment']['vertical'] == 'bottom':
            y_start = player_device.dimensions[1] - \
                margins[1] - \
                life_rank[1] * life_dim[1] * (1 + mirror_styles['padding']['h'])
        else: # center
            y_start = (player_device.dimensions[1] - \
                life_rank[1] * life_dim[1] * (1 + mirror_styles['padding']['h']))/2


        if mirror_styles['stack'] == 'vertical':
            life_rank = (
                life_rank[1],
                life_rank[0]
            )
            
        for row in range(life_rank[1]):
            for col in range(life_rank[0]):

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
                                    life_dim[0]*(1+mirror_styles['padding']['w']),
                                self.life_rendering_points[(row+1)*col - 1][1]
                            )
                        )
                    else:
                        self.life_rendering_points.append(
                            (
                                self.life_rendering_points[(row+1)*col - 1][0] + \
                                    life_dim[0],
                                self.life_rendering_points[(row+1)*col - 1][1] + \
                                    life_dim[1]*(1+mirror_styles['padding']['h'])
                            )
                        )

        self.life_rendering_points.reverse()
            

    def _init_slot_positions(
        self, 
        player_device: device.Device
    ) -> None:
        log.debug('Initializing slot positions on device...', 
            'HUD._init_slot_positions')

        slots_total = self.properties['slots']['total']
        slot_styles = self.styles[self.media_size]['slots']
        x_margins = slot_styles['margins']['w']*player_device.dimensions[0]
        y_margins = slot_styles['margins']['h']*player_device.dimensions[1]

        cap_dim = rotate_dimensions(
            self.hud_conf[self.media_size]['slots']['cap'],
            self.styles[self.media_size]['slots']['stack']
        )
        buffer_dim = rotate_dimensions(
            self.hud_conf[self.media_size]['slots']['buffer'],
            self.styles[self.media_size]['slots']['stack']
        )
        # NOTE: dependent on 'disabled', 'enabled' and 'active' 
        #       being the same dimensions...
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

        # 0    1     2       3     4       5     6       7     8
        # cap, slot, buffer, slot, buffer, slot, buffer, slot, cap
        # number of slots + number of buffers + number of caps
        num = slots_total + (slots_total - 1) + 2
        if slot_styles['stack'] == 'horizontal':
            buffer_correction = (slot_dim[1] - buffer_dim[1])/2
            cap_correction = (slot_dim[1] - cap_dim[1])/2 

            for i in range(num):
                if i == 0: # cap
                    self.slot_rendering_points.append(
                        (
                            x_start, 
                            y_start + cap_correction
                        )
                    )
                elif i == 1: # slot
                    self.slot_rendering_points.append(
                        (
                            self.slot_rendering_points[i-1][0] + cap_dim[0], 
                            y_start
                        )
                    )
                elif i == num - 1: # cap
                    self.slot_rendering_points.append(
                        (
                            self.slot_rendering_points[i-1][0] + slot_dim[0], 
                            y_start + cap_correction
                        )
                    )
                elif i % 2 == 0: # buffer
                    self.slot_rendering_points.append(
                        (
                            self.slot_rendering_points[i-1][0] + slot_dim[0], 
                            y_start + buffer_correction
                        )
                    )
                else: # slot
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
                if i == 0: # cap
                    self.slot_rendering_points.append(
                        (
                            x_start + cap_correction, 
                            y_start
                        )
                    )
                elif i == 1: # slot
                    self.slot_rendering_points.append(
                        (
                            x_start,
                            self.slot_rendering_points[i-1][1] + cap_dim[1]
                        )
                    )
                    self.slot_rendering_points.append(
                        'disabled'
                    )
                elif i == num - 1: # cap
                    self.slot_rendering_points.append(
                        (
                            x_start + cap_correction,
                            self.slot_rendering_points[i-1][1] + slot_dim[1]
                        )
                    )
                elif i % 2 == 0: # buffer
                    self.slot_rendering_points.append(
                        (
                            x_start + buffer_correction,
                            self.slot_rendering_points[i-1][1] + slot_dim[1]
                        )
                    )
                else: # slot
                    self.slot_rendering_points.append(
                        (
                            x_start,
                            self.slot_rendering_points[i-1][1] + buffer_dim[1]
                        )
                    )
                    self.slot_rendering_points.append(
                        'disabled'
                    )

    
    def _init_internal_state(
        self, 
        state_ao: state.State
    ) -> None:
        """Initialize dynamic HUD information from state file.

        :param state_ao: _description_
        :type state_ao: state.State

        .. note:: 
            This method is only used when the class is constructed, since the _World_ at that point is not well defined, (and anyway is not passed into the constructor), so `HUD` properties are hydrated directly from state file on initialization.
        """
        dynamic_state = state_ao.get_state('dynamic')
        self.slots = dynamic_state['hero']['slots']
        self.equipment = dynamic_state['hero']['equipment']
        self.packs = dynamic_state['hero']['packs']
        self.mirrors = {
            'life': dynamic_state['hero']['health']
        }

        self._calculate_slot_frame_map()
        for pack_key in PACK_TYPES:
            self._calculate_pack_frame_map(pack_key)
        for mirror_key in MIRROR_TYPES:
            self._calculate_mirror_frame_map(mirror_key)


    def _calculate_avatar_positions(
        self
    ) -> None:
        """Calculate each _Slot_, _Pack_ and _Wallet_ avatar position
        """

        # TODO: someway to calculate this ... ?
        avatar_render_map = {
            'cast': 2,
            'thrust': 4,
            'slash': 6,
            'shoot': 8
        }

        # NOTE: dependent on 'disabled', 'enabled' and 'active' being the 
        #           same dimensions...
        slot_dim = (
            self.hud_conf[self.media_size]['slots']['disabled']['size']['w'],
            self.hud_conf[self.media_size]['slots']['disabled']['size']['h']
        )

        for i, slot_key in enumerate(self.properties['slots']['maps']):
            if self.slots.get(slot_key):
                slot_point = self.slot_rendering_points[avatar_render_map[slot_key]]
                avatar_dim = (
                    self.avatar_conf['equipment'][self.slots[slot_key]]['size']['w'],
                    self.avatar_conf['equipment'][self.slots[slot_key]]['size']['h']
                )
                self.avatar_rendering_points.append(
                    (
                        slot_point[0] + (slot_dim[0] - avatar_dim[0])/2,
                        slot_point[1] + (slot_dim[1] - avatar_dim[1])/2
                    )
                )
                self.avatar_frame_map[i] = self.slots[slot_key]
            else:
                self.avatar_rendering_points.append(None)
                self.avatar_frame_map[i] = None
        
        # TODO: bag, belt and wallet avatar rendering points


    def _calculate_slot_frame_map(
        self
    ) -> dict:
        # TODO: need to calculate disabled slots from hero state
        #          i.e. will need to pull hero equipment, group by state binding
        #               and see if groups contain enabled equipment
        self.slot_frame_map = {
            key: 'enabled' if val is None else 'active' 
            for key, val in self.slots.items()
        }


    def _calculate_mirror_frame_map(
        self, 
        mirror_key: str
    ) -> dict:
        if mirror_key == 'life':
            self.life_frame_map = {
                i: 'unit' if i <= self.mirrors['life']['current'] - 1 else 'empty'
                for i in range(self.properties['mirrors']['life']['bounds'])
                if i <= self.mirrors['life']['max'] - 1
            }


    def _calculate_pack_frame_map(
        self, 
        pack_key: str
    ) -> dict:
        packset = self.hud_conf[self.media_size]['packs'][pack_key]
        if pack_key in ['bag', 'belt']:
            if pack_key == 'bag':
                self.bag_frame_map = {
                    i: key for i, key in enumerate(packset)
                }
            else:
                self.belt_frame_map = {
                    i: key for i, key in enumerate(packset)
                }
        # TODO: some other way to do this...
        elif pack_key == 'wallet':
            self.wallet_frame_map = {
                0: 'display',
                1: 'display'
            }


    def _calcualte_avatar_frame_map(
        self,
    ) -> dict:
        pass


    def get_frame_map(
        self, 
        hud_key: str
    ) -> list:
        if hud_key == 'life':
            return self.life_frame_map
        if hud_key == 'bag':
            return self.bag_frame_map
        if hud_key == 'belt':
            return self.belt_frame_map
        if hud_key == 'wallet':
            return self.wallet_frame_map
        if hud_key == 'slot':
            return self.slot_frame_map


    def get_cap_directions(
        self
    ) -> str:
        if self.styles[self.media_size]['slots']['stack'] == 'horizontal':
            return ('left', 'right')
        return ('up', 'down')


    def get_buffer_direction(
        self
    ) -> str:
        return self.styles[self.media_size]['slots']['stack']


    def get_buffer_dimensions(
        self
    ) -> tuple:
        return rotate_dimensions(self.hud_conf[self.media_size]['slots']['buffer'])


    def get_cap_dimensions(
        self
    ) -> tuple:
        return rotate_dimensions(self.hud_conf[self.media_size]['slots']['cap'])


    def get_rendering_points(
        self, 
        interface_key: str
    ) -> Union[list, tuple]:
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
        elif interface_key in ['avatar', 'avatars']:
            return self.avatar_rendering_points


    def get_slot_dimensions(
        self
    ) -> tuple:
        return (
            self.hud_conf[self.media_size]['slots']['disabled']['size']['w'], 
            self.hud_conf[self.media_size]['slots']['disabled']['size']['h']
        )


    def update(
        self, 
        game_world: world.World
    ) ->  None:
        avatar_touched = False
        if self.slots != game_world.hero['slots']:
            self.slots = game_world.hero['slots'].copy()
            self._calculate_slot_frame_map()
            avatar_touched = True

        if self.mirrors['life'] != game_world.hero['health']:
            self.mirrors['life'] = game_world.hero['health'].copy()
            self._calculate_mirror_frame_map('life')

        if self.packs['bag'] != game_world.hero['packs']['bag']:
            self.packs['bag'] = game_world.hero['packs']['bag']
            self._calculate_pack_frame_map('bag')
            avatar_touched = True
        
        if self.packs['belt'] != game_world.hero['packs']['belt']:
            self.packs['belt'] = game_world.hero['packs']['belt']
            self._calculate_pack_frame_map('belt')
            avatar_touched = True

        if avatar_touched:
            self._calculate_avatar_positions()


    def toggle_hud(
        self
    ) -> None:
        self.hud_activated = not self.hud_activated

    
    def get_slot(
        self,
        slot_key: str
    ) -> Union[str, None]:
        return self.slots.get(slot_key)


    def get_pack(
        self,
        pack_key: str
    ) -> Union[str, None]:
        return self.packs.get(pack_key)

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


    def _init_conf(
        self, 
        config: conf.Conf
    ) -> None:
        self.menu_conf = config['menu']
        self.sizes = config['sizes']
        self.styles = config['styles']
        self.properties = config['properties']['menu']
        self.breakpoints = format_breakpoints(config['breakpoints'])
        self.tabs = {
            button_name: {} 
            for button_name in self.properties['button']['buttons']
        }


    def _init_menu_positions(
        self, 
        player_device: device.Device
    ) -> None:
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


    def _init_buttons(
        self, 
        state_ao: state.State
    ) -> None:
        """_summary_

        :param state_ao: _description_
        :type state_ao: state.State
        """
        # TODO: calculate based on state information

        for i, name in enumerate(self.properties['button']['buttons']):
            if i == 0:
                self._activate_button(name)
                self.active_button = i
            else:
                self._enable_button(name)


    def _activate_button(
        self, 
        button_key: str
    ) -> None:
        """_summary_

        :param button_key: _description_
        :type button_key: str
        """
        self.buttons[button_key] = {
            piece: 'active' 
            for piece in self.properties['button']['pieces']
        }


    def _disable_button(
        self, 
        button_key: str
    ) -> None:
        """_summary_

        :param button_key: _description_
        :type button_key: str
        """
        self.buttons[button_key] = {
            piece: 'disabled' 
            for piece in self.properties['button']['pieces']
        }


    def _enable_button(
        self, 
        button_key: str
    ) -> None:
        """_summary_

        :param button_key: _description_
        :type button_key: str
        """
        self.buttons[button_key] = {
            piece: 'enabled' 
            for piece in self.properties['button']['pieces']
        }


    def _increment_active_button(
        self
    ) -> None:
        """_summary_
        """
        ## TODO: skip disabled buttons
        previous_active = self.active_button
        self.active_button -= 1

        if self.active_button < 0:
            self.active_button = len(self.properties['button']['buttons']) - 1
        
        self._enable_button(self.properties['button']['buttons'][previous_active])
        self._activate_button(self.properties['button']['buttons'][self.active_button])


    def _decrement_active_button(
        self
    ) -> None:
        """_summary_
        """
        ## TODO: skip disabled buttons
        previous_active = self.active_button
        self.active_button += 1

        if self.active_button > len(self.properties['button']['buttons']) - 1:
            self.active_button = 0
        
        self._enable_button(self.properties['button']['buttons'][previous_active])
        self._activate_button(self.properties['button']['buttons'][self.active_button])


    def execute_active_button(
        self
    ):
        pass


    def button_frame_map(
        self
    ) -> list:
        frame_map = []
        for piece_conf in self.buttons.values():
            for piece_state in piece_conf.values():
                frame_map.append(piece_state)
        return frame_map


    def button_piece_map(
        self
    ) -> list:
        piece_map = []
        for piece_conf in self.buttons.values():
            for piece_key in piece_conf.keys():
                piece_map.append(piece_key)
        return piece_map


    def button_maps(
        self
    ) -> tuple:
        return (self.button_frame_map(), self.button_piece_map())


    def toggle_menu(
        self
    ) -> None:
        self.menu_activated = not self.menu_activated


    def get_rendering_points(
        self, 
        interface_key: str
    ) -> list:
        if interface_key in [ 'button', 'buttons' ]:
            return self.button_rendering_points


    def update(
        self, 
        user_input: dict
    ) -> None:
        if user_input['n']:
            self._increment_active_button()
        elif user_input['s']:
            self._decrement_active_button()