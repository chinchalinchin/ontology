from typing import Union

import munch
from onta.engine.static import formulae
import onta.settings as settings
import onta.device as device
import onta.world as world
import onta.loader.conf as conf
import onta.loader.state as state
import onta.util.logger as logger
import onta.engine.senses.display as display

log = logger.Logger('onta.engine.senses.hud', settings.LOG_LEVEL)

PACK_TYPES = [ 'bag', 'belt', 'wallet' ]
MIRROR_TYPES = [ 'life', 'magic' ]

class HUD():
    """
    
    .. note::
        Frame maps and frame rendering points are kept as separate data structures due to the fact that frame maps are dynamically update according to the world state, whereas rendering points are static.
    """

    hud_conf = munch.Munch({})
    """
    ```python
    ```
    """
    avatar_conf = munch.Munch({})
    """
    ```python
    ```
    """
    styles = munch.Munch({})
    """
    ```python
    ```
    """
    properties = munch.Munch({})
    """
    ```python
    ```
    """
    slots = munch.Munch({})
    """
    ```python
    ```
    """
    mirrors = munch.Munch({})
    """
    ```python
    ```
    """
    packs = munch.Munch({})
    """
    ```python
    ```
    """
    equipment = munch.Munch({})
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
    avatar_frame_map = munch.Munch({})
    pack_frame_map = munch.Munch({})
    slot_frame_map = munch.Munch({})
    life_frame_map = munch.Munch({})
    belt_frame_map = munch.Munch({})
    bag_frame_map = munch.Munch({})
    wallet_frame_map = munch.Munch({})

    slot_dimensions = None
    bag_dimensions = None
    belt_dimensions = None
    wallet_dimensions = None
    life_dimensions = None
    magic_dimensions = None

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


    def _immute_slots(
        self
    ):
        return tuple([ 
            ( key, value ) 
            if value else
            ( key , 'null' )
            for key, value in self.slots.items()
        ])


    def _immute_equipment_size(
        self
    ):
        return tuple([
            (
                equip_key, 
                equip.size.w, 
                equip.size.h
            )
            for equip_key, equip in self.avatar_conf.equipment.items()
            if equip is not None and equip.get('size') is not None
        ])

    def _immute_inventory_size(
        self
    ):
        return tuple([
            (
                invent_key, 
                invent.size.w, 
                invent.size.h
            )
            for invent_key, invent in self.avatar_conf.inventory.items()
            if invent is not None and invent.get('size') is not None
        ])


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

        self.styles = sense_config.styles
        self.hud_conf = sense_config.hud
        self.sizes = sense_config.sizes
        self.breakpoints = display.format_breakpoints(sense_config.breakpoints)
        self.properties = sense_config.properties
        self.media_size = display.find_media_size(
            player_device, 
            self.sizes, 
            self.breakpoints
        )

        self.avatar_conf = config.load_avatar_configuration().avatars


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
            self.styles.get(self.media_size).packs.margins.w, 
            self.styles.get(self.media_size).packs.margins.h
        )
        pack_horizontal_align = self.styles.get(self.media_size).packs.alignment.horizontal
        pack_vertical_align = self.styles.get(self.media_size).packs.alignment.vertical

        bagset = self.hud_conf.get(self.media_size).packs.bag
        bag_dim = self.get_bag_dimensions()

        # (0, left), (1, right)
        for i, bag_piece in enumerate(bagset.values()):
            if i == 0:
                if pack_horizontal_align == 'left':
                    x = pack_margins[0] * player_device.dimensions[0]
                elif pack_horizontal_align == 'right':
                    x = ( 1 - pack_margins[0] ) * player_device.dimensions[0] - \
                        bag_dim[0]

                if pack_vertical_align == 'top':
                    y = pack_margins[1]*player_device.dimensions[1]
                elif pack_vertical_align == 'bottom':
                    y = ( 1 - pack_margins[0] ) * player_device.dimensions[1] - \
                        bag_dim[0]
            else:
                x = self.bag_rendering_points[i-1][0] + prev_w
                y = self.bag_rendering_points[i-1][1]
            self.bag_rendering_points.append((x,y))
            prev_w = bag_piece.size.w

        beltset = self.hud_conf.get(self.media_size).packs.belt
        belt_dim = self.get_belt_dimensions()

        # belt initial position only affected by pack vertical alignment
        for i, belt_piece in enumerate(beltset.values()):
            if i == 0:
                if pack_horizontal_align == 'left':
                    # dependent on bag height > belt height
                    x = self.bag_rendering_points[0][0] + \
                            ( 1 + pack_margins[0] ) * bag_dim[0]
                    y = self.bag_rendering_points[0][1] + \
                            ( bag_dim[1] - belt_dim[1] )/2
                elif pack_horizontal_align == 'right':
                    x = self.bag_rendering_points[0][0] - \
                            ( 1 + pack_margins[0] ) * bag_dim[0]
                    y = self.bag_rendering_points[0][1] + \
                            ( bag_dim[1] - belt_dim[1] )/2  
            else:
                x = self.belt_rendering_points[i-1][0] + prev_w
                y = self.belt_rendering_points[i-1][1]
            self.belt_rendering_points.append(
                (x,y)
            )
            prev_w = belt_piece.size.w
        

        wallet_dim = self.get_wallet_dimensions()

        if pack_horizontal_align == 'left':
            self.wallet_rendering_points.append(
                (
                    self.belt_rendering_points[0][0] + \
                        (
                            belt_dim[0] + pack_margins[0] * ( bag_dim[0] + belt_dim[0] )
                        ),
                    self.bag_rendering_points[0][1] + \
                        (
                            belt_dim[1] - wallet_dim[1] * (2 + pack_margins[1]) 
                        )/2
                )
            )
        elif pack_horizontal_align == 'right':
            self.wallet_rendering_points.append(
                (
                    self.bag_rendering_points[0][0] - \
                        (
                            belt_dim[0] + pack_margins[0] * ( bag_dim[0] + belt_dim[0] )
                        ) - wallet_dim[0],
                    self.bag_rendering_points[0][1] + \
                        (
                            belt_dim[1] - wallet_dim[1] * ( 2 + pack_margins[1] )
                        ) / 2
                )
            )
        self.wallet_rendering_points.append(
            (
                self.wallet_rendering_points[0][0],
                self.wallet_rendering_points[0][1] + \
                    ( 1 + pack_margins[1] ) * wallet_dim[0]
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
        mirror_styles = self.styles.get(self.media_size).mirrors
        life_rank = (
            self.properties.mirrors.life.columns,
            self.properties.mirrors.life.rows,
        )
        # NOTE: dependent on 'unit' and 'empty' being the same dimensions...
        life_dim = (
            self.hud_conf.get(self.media_size).mirrors.life.unit.size.w,
            self.hud_conf.get(self.media_size).mirrors.life.unit.size.h
        )
        margins= (
            mirror_styles.margins.w * player_device.dimensions[0],
            mirror_styles.margins.h * player_device.dimensions[1]
        )

        if mirror_styles.alignment.horizontal == 'right':
            x_start = player_device.dimensions[0] - \
                margins[0] - \
                life_rank[0] * life_dim[0]*(1 + mirror_styles.padding.w) 
        elif mirror_styles.alignment.horizontal == 'left':
            x_start = margins[0]
        else: # center
            x_start = (player_device.dimensions[0] - \
                life_rank[0] * life_dim[0] *(1 + mirror_styles.padding.w))/2
        
        if mirror_styles.alignment.vertical == 'top':
            y_start = margins[1]
        elif mirror_styles.alignment.vertical == 'bottom':
            y_start = player_device.dimensions[1] - \
                margins[1] - \
                life_rank[1] * life_dim[1] * (1 + mirror_styles.padding.h)
        else: # center
            y_start = (player_device.dimensions[1] - \
                life_rank[1] * life_dim[1] * (1 + mirror_styles.padding.h))/2


        if mirror_styles.stack == 'vertical':
            life_rank = (life_rank[1], life_rank[0])
            
        for row in range(life_rank[1]):
            for col in range(life_rank[0]):

                if (row+1)*col == 0:
                    self.life_rendering_points.append(
                        ( x_start, y_start)
                    )
                else:
                    if mirror_styles.stack == 'horizontal':
                        self.life_rendering_points.append(
                            (
                                self.life_rendering_points[(row+1)*col - 1][0] + \
                                    life_dim[0]*(1+mirror_styles.padding.w),
                                self.life_rendering_points[(row+1)*col - 1][1]
                            )
                        )
                    else:
                        self.life_rendering_points.append(
                            (
                                self.life_rendering_points[(row+1)*col - 1][0] + \
                                    life_dim[0],
                                self.life_rendering_points[(row+1)*col - 1][1] + \
                                    life_dim[1]*(1+mirror_styles.padding.h)
                            )
                        )

        self.life_rendering_points.reverse()
            

    def _init_slot_positions(
        self, 
        player_device: device.Device
    ) -> None:
        log.debug('Initializing slot positions on device...', 'HUD._init_slot_positions')

        slots_total = self.properties.slots.total
        slot_styles = self.styles.get(self.media_size).slots
        x_margins = slot_styles.margins.w * player_device.dimensions[0]
        y_margins = slot_styles.margins.h * player_device.dimensions[1]

        cap_dim = display.rotate_dimensions(
            self.hud_conf.get(self.media_size).slots.cap,
            self.styles.get(self.media_size).slots.stack
        )
        buffer_dim = display.rotate_dimensions(
            self.hud_conf.get(self.media_size).slots.buffer,
            self.styles.get(self.media_size).slots.stack
        )
        # NOTE: dependent on 'disabled', 'enabled' and 'active' 
        #       being the same dimensions...
        slot_dim = (
            self.hud_conf.get(self.media_size).slots.disabled.size.w,
            self.hud_conf.get(self.media_size).slots.disabled.size.h
        )

        if slot_styles.alignment.horizontal == 'right':
            x_start = player_device.dimensions[0] \
                - x_margins \
                - slots_total*slot_dim[0] \
                - (slots_total-1)*buffer_dim[0] \
                - 2*cap_dim[0]
        elif slot_styles.alignment.horizontal == 'center':
            x_start = (player_device.dimensions[0] \
                - slots_total*slot_dim[0] \
                - (slots_total-1)*buffer_dim[0] \
                - 2*cap_dim[0])/2
                
        else: # left
            x_start = x_margins

                
        if slot_styles.alignment.vertical == 'bottom':
            if slot_styles.stack == 'horizontal':
                y_start = player_device.dimensions[1] \
                    - y_margins \
                    - slot_dim[1] 
            elif slot_styles.stack == 'vertical':
                y_start = player_device.dimensions[1] \
                    - y_margins \
                    - slots_total*slot_dim[1] \
                    - (slots_total-1)*buffer_dim[1] \
                    - 2*cap_dim[1]
        elif slot_styles.alignment.vertical == 'center':
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
        if slot_styles.stack == 'horizontal':
            buffer_correction = (slot_dim[1] - buffer_dim[1])/2
            cap_correction = (slot_dim[1] - cap_dim[1])/2 

            for i in range(num):
                if i == 0: # cap
                    self.slot_rendering_points.append(
                        ( x_start, y_start + cap_correction )
                    )
                elif i == 1: # slot
                    self.slot_rendering_points.append(
                        ( self.slot_rendering_points[i-1][0] + cap_dim[0], y_start )
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
                        ( self.slot_rendering_points[i-1][0] + buffer_dim[0], y_start )
                    )

        elif slot_styles.stack == 'vertical':
            buffer_correction = (slot_dim[0] - buffer_dim[0])/2
            cap_correction = (slot_dim[0] - cap_dim[0])/2
            for i in range(num):
                if i == 0: # cap
                    self.slot_rendering_points.append(
                        ( x_start + cap_correction, y_start )
                    )
                elif i == 1: # slot
                    self.slot_rendering_points.append(
                        ( x_start, self.slot_rendering_points[i-1][1] + cap_dim[1] )
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
        self.slots = dynamic_state.hero.slots
        self.equipment = dynamic_state.hero.inventory.equipment
        self.packs = dynamic_state.hero.packs
        setattr(self.mirrors, 'life', dynamic_state.hero.health)

        self._calculate_slot_frame_map()
        for pack_key in PACK_TYPES:
            self._calculate_pack_frame_map(pack_key)
        for mirror_key in MIRROR_TYPES:
            self._calculate_mirror_frame_map(mirror_key)


    def _calculate_avatar_positions(
        self
    ) -> None:
        """Calculate each _Slot_, _Pack_ and _Wallet_ avatar positions
        """
        # TODO: must be a better way to calculate this...
        avatar_tuple =(
            ('cast', 1),
            ('thrust', 3),
            ('shoot', 5),
            ('slash',7 )
        )

            # jitting ain't easy...
        render_tuples = formulae.slot_avatar_coordinates(
            self._immute_slots(), 
            self._immute_equipment_size(),
            self._immute_inventory_size(),
            tuple(self.slot_rendering_points),
            tuple(self.bag_rendering_points),
            tuple(self.belt_rendering_points),
            tuple(self.properties.slots.maps),
            avatar_tuple, 
            self.packs.bag,
            self.packs.belt, 
            self.get_slot_dimensions(),
            self.get_bag_dimensions(),
            self.get_belt_dimensions(),
        )
        self.avatar_rendering_points = []

        for i in range(len(render_tuples)):

            if render_tuples[i][0] != -1:
                self.avatar_rendering_points.append(
                    render_tuples[i]
                )
            else:
                self.avatar_rendering_points.append(
                    None
                )
            
            if i < len(self.properties.slots.maps):
                setattr(
                    self.avatar_frame_map, 
                    str(i), 
                    self.slots.get(self.properties.slots.maps[i])
                )

        setattr(
            self.avatar_frame_map,
            str(len(self.avatar_frame_map)),
            self.packs.bag
        )
        setattr(
            self.avatar_frame_map,
            str(len(self.avatar_frame_map)),
            self.packs.belt
        )
        # TODO: wallet avatar rendering points


    def _calculate_slot_frame_map(
        self
    ) -> munch.Munch:
        # TODO: need to calculate disabled slots from hero state
        #          i.e. will need to pull hero equipment, group by state binding
        #               and see if groups contain enabled equipment
        # TODO: use active if hero currently in that state!!!
        self.slot_frame_map = munch.Munch({
            key: 'disabled' if val is None else 'enabled' 
            for key, val in self.slots.items()
        })


    def _calculate_mirror_frame_map(
        self, 
        mirror_key: str
    ) -> dict:
        if mirror_key == 'life':
            self.life_frame_map = munch.Munch({
                i: 'unit' if i <= self.mirrors.life.current - 1 else 'empty'
                for i in range(self.properties.mirrors.life.bounds)
                if i <= self.mirrors.life.max - 1
            })


    def _calculate_pack_frame_map(
        self, 
        pack_key: str
    ) -> dict:
        packset = self.hud_conf.get(self.media_size).packs.get(pack_key)
        if pack_key in ['bag', 'belt']:
            if pack_key == 'bag':
                self.bag_frame_map = munch.Munch({
                    i: key for i, key in enumerate(packset)
                })
            else:
                self.belt_frame_map = munch.Munch({
                    i: key for i, key in enumerate(packset)
                })
        # TODO: some other way to do this...
        elif pack_key == 'wallet':
            self.wallet_frame_map = munch.Munch({
                0: 'display',
                1: 'display'
            })


    def _calcualte_avatar_frame_map(
        self,
    ) -> dict:
        # start with slots...
        pass


    def get_frame_map(
        self, 
        hud_key: str
    ) -> munch.Munch:
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
        if hud_key == 'avatar':
            return self.avatar_frame_map


    def get_cap_directions(
        self
    ) -> str:
        if self.styles.get(self.media_size).slots.stack == 'horizontal':
            return ('left', 'right')
        return ('up', 'down')


    def get_buffer_direction(
        self
    ) -> str:
        return self.styles.get(self.media_size).slots.stack


    def get_buffer_dimensions(
        self
    ) -> tuple:
        return display.rotate_dimensions(
            self.hud_conf.get(self.media_size).slots.buffer
        )


    def get_cap_dimensions(
        self
    ) -> tuple:
        return display.rotate_dimensions(
            self.hud_conf.get(self.media_size).slots.cap
        )


    def get_bag_dimensions(
        self
    ) -> tuple:
        if not self.bag_dimensions:
            bagset = self.hud_conf.get(self.media_size).packs.bag

            total_bag_width = 0
            for bag_piece in bagset.values():
                total_bag_width += bag_piece.size.w

            # dependent on both pieces being the same height
            # i.e., the pack sheet can only be broken in the 
            # horizontal direction
            total_bag_height = bagset.get(list(bagset.keys())[0]).size.h

            self.bag_dimensions = ( total_bag_width, total_bag_height )
        return self.bag_dimensions


    def get_belt_dimensions(
        self
    ) -> tuple:
        if not self.belt_dimensions:
            beltset = self.hud_conf.get(self.media_size).packs.belt

            total_belt_width = 0
            for belt_piece in beltset.values():
                total_belt_width += belt_piece.size.w
            total_belt_height = beltset.get(list(beltset.keys())[0]).size.h

            self.belt_dimensions = ( total_belt_width, total_belt_height )
        return self.belt_dimensions


    def get_wallet_dimensions(
        self
    ) -> tuple:
        if not self.wallet_dimensions:
            self.wallet_dimensions = (
                self.hud_conf.get(self.media_size).packs.wallet.display.size.w, 
                self.hud_conf.get(self.media_size).packs.wallet.display.size.h
            )
        return self.wallet_dimensions


    def get_rendering_points(
        self, 
        interface_key: str
    ) -> list:
        if interface_key  == 'slot':
            return self.slot_rendering_points
        elif interface_key == 'life':
            return self.life_rendering_points    
        elif interface_key == 'bag':
            return self.bag_rendering_points
        elif interface_key == 'wallet':
            return self.wallet_rendering_points
        elif interface_key == 'belt':
            return self.belt_rendering_points
        elif interface_key == 'avatar':
            return self.avatar_rendering_points


    def get_slot_dimensions(
        self
    ) -> tuple:
        return (
            self.hud_conf.get(self.media_size).slots.disabled.size.w, 
            self.hud_conf.get(self.media_size).slots.disabled.size.h
        )


    def update(
        self, 
        game_world: world.World
    ) ->  None:
        avatar_touched = False
        if self.slots != game_world.hero.slots:
            self.slots = game_world.hero.slots.copy()
            self._calculate_slot_frame_map()
            avatar_touched = True

        if self.mirrors.life != game_world.hero.health:
            setattr(self.mirrors, 'life', game_world.hero.health.copy())
            self._calculate_mirror_frame_map('life')

        if self.packs.bag != game_world.hero.packs.bag:
            setattr(self.packs, 'bag', game_world.hero.packs.bag)
            self._calculate_pack_frame_map('bag')
            avatar_touched = True
        
        if self.packs.belt != game_world.hero.packs.belt:
            self.packs.belt = game_world.hero.packs.belt
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
