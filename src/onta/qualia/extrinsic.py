import munch
from typing \
    import Union

from onta \
    import world
from onta.actuality \
    import state, conf
from onta.concretion.facticity \
    import formulae
from onta.metaphysics \
    import logger, settings, device, constants
from onta.qualia \
    import apriori

log = logger.Logger(
    'onta.concretion.qualia.extrinsic', 
    settings.LOG_LEVEL
)

class ExtrinsicQuale():
    """
    An `ExtrinsicQuale` is essentially a super-pretentious name for a Headsup Display.

    .. note::
        Frame maps and frame rendering points are kept as separate data structures due to the fact that frame maps are dynamically update according to the world state, whereas rendering points are static.
    """


    @staticmethod
    def immute_slots(
        slot_configuration
    ):
        return tuple(
            ( 
                key, 
                value 
            ) 
            if value else
            ( 
                key , 
                'null' 
            )
            for key, value 
            in slot_configuration.items()
        )


    @staticmethod
    def immute_armory_size(
        avatar_configuration
    ):
        return tuple(
            (
                equip_key, 
                equip.size.w, 
                equip.size.h
            )
            for equip_key, equip 
            in avatar_configuration.armory.items()
            if equip is not None 
            and equip.get('size') is not None
        )


    @staticmethod
    def immute_inventory_size(
        avatar_configuration
    ):
        return tuple(
            (
                invent_key, 
                invent.size.w, 
                invent.size.h
            )
            for invent_key, invent 
            in avatar_configuration.inventory.items()
            if invent is not None 
            and invent.get('size') is not None
        )

    def __init__(
        self, 
        player_device: device.Device, 
        ontology_path: str = settings.DEFAULT_DIR
    ) -> None:
        config = conf.Conf(ontology_path)
        state_ao = state.State(ontology_path)
        self._init_fields()
        self._init_conf(
            config, 
            player_device
        )
        self._init_slot_positions(player_device)
        self._init_mirror_positions(player_device)
        self._init_pack_positions(player_device)
        self._init_internal_state(state_ao)
        self._calculate_avatar_positions()


    def _init_fields(
        self
    ) -> None:
        """
        .. note::
            ```python
            self.quale_conf = {
                # TODO:
            }
            self.render_points = {
                # TODO:
                'avatar': [
                    slot_1_avatar_pt, # tuple
                    slot_2_avatar_pt, # tuple
                    slot_3_avatar_pt, # tuple,
                    slot_4_avatar_pt, # tuple
                    bag_avatar_pt, # tuple
                    belt_avatar_pt, # tuple
                    wallet_coin_avatar_pt, # tuple
                    wallet_key_avatar_pt, # tuple
                ],
                # ...
            ```
        """
        self.containers = munch.Munch({})
        self.render_points = munch.Munch({})
        self.frame_maps = munch.Munch({})
        self.dimensions = munch.Munch({})
        self.quale_activated = True


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

        .. note::
            ```python
            ```
        """
        configure = config.load_qualia_configuration()

        self.quale_conf = configure.qualia
        self.sizes = configure.apriori.sizes
        self.breakpoints = apriori.format_breakpoints(
            configure.apriori.breakpoints
        )    
        self.media_size = apriori.find_media_size(
            player_device.dimensions, 
            self.sizes, 
            self.breakpoints
        )
        self.properties = configure.properties
        self.styles = configure.styles.get(self.media_size)

        self.avatar_conf = config.load_avatar_configuration()


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
        log.debug(
            'Initializing pack positions on device...', 
            'ExtrinsicQuale._init_pack_positions'
        )

        pack_margins = (
            self.styles.pack.margins.w, 
            self.styles.pack.margins.h
        )
        pack_alignment = (
            self.styles.pack.alignment.horizontal,
            self.styles.pack.alignment.vertical
        )

        bagset = self.quale_conf.piecwise.bag
        beltset = self.quale_conf.piecewise.belt

        bag_piece_sizes = tuple(
            (
                bag_piece.size.w, 
                bag_piece.size.h
            ) for bag_piece in list(bagset.values())
        )
        belt_piece_sizes = tuple(
            (
                belt_piece.size.w, 
                belt_piece.size.h
            ) for belt_piece in list(beltset.values())
        )

        setattr(
            self.render_points,
            constants.QualiaType.BAG.value,
            formulae.bag_coordinates(
                bag_piece_sizes,
                self.get_bag_dimensions(),
                pack_alignment,
                pack_margins,
                player_device.dimensions,
            )
        )

        setattr(
            self.render_points,
            constants.QualiaType.BELT.value,
            formulae.belt_coordinates(
                self.render_points.bag[0],
                belt_piece_sizes,
                self.get_belt_dimensions(),
                pack_alignment[0],
                pack_margins,
                self.get_bag_dimensions(),
                self.get_bag_dimensions()
            )
        )

        setattr(
            self.render_points,
            constants.QualiaType.WALLET.value,
            formulae.wallet_coordinates(
                self.render_points.belt[0],
                self.render_points.bag[0],
                self.get_bag_dimensions(),
                self.get_belt_dimensions(),
                self.get_wallet_dimensions(),
                pack_alignment[0],
                pack_margins
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
        log.debug(
            'Initializing mirror positions on device...', 
            'ExtrinsicQuale._init_mirror_positions'
        )

        mirror_styles = self.styles.get(self.media_size).mirror
       
        mirror_alignment = (
            self.styles.get(self.media_size).mirror.alignment.horizontal,
            self.styles.get(self.media_size).mirror.alignment.vertical
        )

        life_rank = (
            self.properties.mirror.life.columns,
            self.properties.mirror.life.rows,
        )

        # NOTE: dependent on 'unit' and 'empty' being the same dimensions...

        life_dim = (
            self.quale_conf.get(self.media_size).mirror.life.unit.size.w,
            self.quale_conf.get(self.media_size).mirror.life.unit.size.h
        )

        margins= (
            mirror_styles.margins.w * player_device.dimensions[0],
            mirror_styles.margins.h * player_device.dimensions[1]
        )

        padding = (
            mirror_styles.padding.w,
            mirror_styles.padding.h
        )

        setattr(
            self.render_points,
            'life',
            formulae.life_mirror_coordinates(
                player_device.dimensions,
                mirror_alignment,
                mirror_styles.stack,
                margins,
                padding,
                life_rank,
                life_dim
            )
        )
   

    def _init_slot_positions(
        self, 
        player_device: device.Device
    ) -> None:
        log.debug(
            'Initializing slot positions on device...', 
            'ExtrinsicQuale._init_slot_positions'
        )

        slots_total = self.properties.slot.total
        slot_styles = self.styles.get(self.media_size).slot

        alignment = (
            slot_styles.alignment.horizontal,
            slot_styles.alignment.vertical
        )
        margins = (
            slot_styles.margins.w,
            slot_styles.margins.h
        )

        cap_dim = formulae.rotate_dimensions(
            (
                self.quale_conf.get(self.media_size).slot.cap.size.w,
                self.quale_conf.get(self.media_size).slot.cap.size.h
            ),
            self.quale_conf.get(self.media_size).slot.cap.definition,
            self.styles.get(self.media_size).slot.stack
        )

        buffer_dim = formulae.rotate_dimensions(
            (
                self.quale_conf.get(self.media_size).slot.buffer.size.w,
                self.quale_conf.get(self.media_size).slot.buffer.size.h
            ),
            self.quale_conf.get(self.media_size).slot.buffer.definition,
            self.styles.get(self.media_size).slot.stack
        )

        slot_dim = (
            self.quale_conf.get(self.media_size).slot.disabled.size.w,
            self.quale_conf.get(self.media_size).slot.disabled.size.h
        )

        setattr(
            self.render_points,
            'slot',
            formulae.slot_coordinates(
                slots_total,
                slot_dim,
                buffer_dim,
                cap_dim,
                player_device.dimensions,
                alignment,
                margins,
                slot_styles.stack,
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
        setattr(
            self.containers,
            'slots',
            state_ao.get_state('dynamic').hero.slots
        )
        setattr(
            self.containers,
            'equipment',
            state_ao.get_state('dynamic').hero.capital.equipment
        )
        setattr(
            self.containers,
            'packs',
            state_ao.get_state('dynamic').hero.packs
        )
        setattr(
            self.containers,
            'mirrors',
            munch.Munch({
                'life': state_ao.get_state('dynamic').hero.health
            })
        )

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
        # TODO: must be a way to calculate this rather than declare it...
        avatar_tuple =(
            ( 
                'cast', 
                1 
            ),
            ( 
                'thrust', 
                3 
            ),
            ( 
                'shoot', 
                5 
            ),
            ( 
                'slash', 
                7 
            )
        )

        # NOTE: this ugliness is all in service of immutability...
        setattr(
            self.render_points,
            'avatar',
            formulae.slot_avatar_coordinates(
                ExtrinsicQuale.immute_slots(self.containers.slots), 
                ExtrinsicQuale.immute_armory_size(self.avatar_conf),
                ExtrinsicQuale.immute_inventory_size(self.avatar_conf),
                tuple(self.render_points.slot),
                tuple(self.render_points.bag),
                tuple(self.render_points.belt),
                tuple(self.properties.slot.maps),
                avatar_tuple, 
                self.containers.packs.bag,
                self.containers.packs.belt, 
                self.get_slot_dimensions(),
                self.get_bag_dimensions(),
                self.get_belt_dimensions(),
            )
        )

        setattr(self.frame_maps, 'avatar', munch.Munch({}))

        for i, _ in enumerate(self.render_points.avatar):
            if i < len(self.properties.slot.maps):
                setattr(
                    self.frame_maps.avatar, 
                    str(i), 
                    self.containers.slots.get(
                        self.properties.slot.maps[i]
                    )
                )

        setattr(
            self.frame_maps.avatar,
            str(
                len(self.frame_maps.avatar)
            ),
            self.containers.packs.bag
        )
        setattr(
            self.frame_maps.avatar,
            str(
                len(self.frame_maps.avatar)
            ),
            self.containers.packs.belt
        )
        # TODO: wallet avatar rendering points


    def _calculate_slot_frame_map(
        self
    ) -> munch.Munch:
        # TODO: need to calculate disabled slots from hero state
        #          i.e. will need to pull hero equipment, group by state binding
        #               and see if groups contain enabled equipment
        # TODO: use active if hero currently in that state!!!

        setattr(
            self.frame_maps,
            'slot',
            munch.Munch({
                key: 'disabled' 
                if val is None 
                else 'enabled' 
                for key, val 
                in self.containers.slots.items()
            })
        )


    def _calculate_mirror_frame_map(
        self, 
        mirror_key: str
    ) -> dict:
        if mirror_key == 'life':
            setattr(
                self.frame_maps,
                'life',
                munch.Munch({
                    i: 'unit' 
                    if i <= self.containers.mirrors.life.current - 1 
                    else 'empty'
                    for i in range(
                        self.properties.mirror.life.bounds
                    )
                    if i <= self.containers.mirrors.life.max - 1
                })
            )


    def _calculate_pack_frame_map(
        self, 
        pack_key: str
    ) -> dict:
        # TODO: this could be a lookup instead of a switch statement...
        packset = self.quale_conf.get(self.media_size).pack.get(pack_key)
        if pack_key in [ 'bag', 'belt' ]:
            setattr(
                self.frame_maps,
                pack_key,
                munch.Munch({
                    i: key 
                    for i, key 
                    in enumerate(packset)
                })
            )

        # TODO: some other way to do this...
        elif pack_key == 'wallet':
            self.wallet_frame_map = munch.Munch({
                0: 'display',
                1: 'display'
            })


    def get_frame_map(
        self, 
        component_key: str
    ) -> munch.Munch:
        return self.frame_maps.get(component_key)


    def get_cap_directions(
        self
    ) -> str:
        if self.styles.get(self.media_size).slot.stack == 'horizontal':
            return (
                'left', 
                'right'
            )
        return (
            'up', 
            'down'
        )


    def get_buffer_direction(
        self
    ) -> str:
        return self.styles.get(self.media_size).slot.stack


    def get_bag_dimensions(
        self
    ) -> tuple:
        if not self.dimensions.get('bag'):
            bagset = self.quale_conf.get(self.media_size).pack.bag.display

            total_bag_width = 0
            for bag_piece in bagset.values():
                total_bag_width += bag_piece.size.w

            # dependent on both pieces being the same height
            # i.e., the pack sheet can only be broken in the 
            # horizontal direction
            total_bag_height = bagset.get(
                list(bagset.keys())[0]
            ).size.h

            setattr(
                self.dimensions,
                'bag',
                ( 
                    total_bag_width, 
                    total_bag_height 
                )
            )
        return self.dimensions.bag


    def get_belt_dimensions(
        self
    ) -> tuple:
        if not self.dimensions.get('belt'):
            beltset = self.quale_conf.get(self.media_size).pack.belt.display

            total_belt_width = 0
            for belt_piece in beltset.values():
                total_belt_width += belt_piece.size.w
            total_belt_height = beltset.get(
                list(beltset.keys())[0]
            ).size.h

            setattr(
                self.dimensions,
                'belt',
                ( 
                    total_belt_width, 
                    total_belt_height 
                )
            )
        return self.dimensions.belt


    def get_wallet_dimensions(
        self
    ) -> tuple:
        if not self.dimensions.get('wallet'):
            setattr(
                self.dimensions,
                'wallet',
                (
                    self.quale_conf.get(self.media_size).pack.wallet.display.size.w, 
                    self.quale_conf.get(self.media_size).pack.wallet.display.size.h
                )
            )
        return self.dimensions.wallet


    def get_slot_dimensions(
        self
    ) -> tuple:
        if not self.dimensions.get('slot'):
            setattr(
                self.dimensions,
                'slot',
                (
                    self.quale_conf.get(self.media_size).slot.disabled.size.w, 
                    self.quale_conf.get(self.media_size).slot.disabled.size.h
                )
            )
        return self.dimensions.slot


    def get_render_points(
        self, 
        component_key: str
    ) -> list:
        return self.render_points.get(component_key)


    def update(
        self, 
        game_world: world.World
    ) ->  None:
        avatar_touched = False
        if self.containers.slots != game_world.hero.slots:
            setattr(
                self.containers,
                'slots',
                game_world.hero.slots.copy()
            )
            self._calculate_slot_frame_map()
            avatar_touched = True

        if self.containers.mirrors.life != game_world.hero.health:
            setattr(
                self.containers.mirrors, 
                'life', 
                game_world.hero.health.copy()
            )
            self._calculate_mirror_frame_map('life')

        if self.containers.packs.bag != game_world.hero.packs.bag:
            setattr(
                self.containers.packs, 
                'bag', 
                game_world.hero.packs.bag
            )
            self._calculate_pack_frame_map('bag')
            avatar_touched = True
        
        if self.containers.packs.belt != game_world.hero.packs.belt:
            self.containers.packs.belt = game_world.hero.packs.belt
            self._calculate_pack_frame_map('belt')
            avatar_touched = True

        if avatar_touched:
            self._calculate_avatar_positions()


    def toggle_quale(
        self
    ) -> None:
        self.quale_activated = not self.quale_activated

    
    def get_slot(
        self,
        slot_key: str
    ) -> Union[
        str, 
        None
    ]:
        return self.containers.slots.get(slot_key)


    def get_pack(
        self,
        pack_key: str
    ) -> Union[
        str, 
        None
    ]:
        return self.containers.packs.get(pack_key)
