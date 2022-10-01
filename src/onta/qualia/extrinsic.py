import munch
from typing \
    import Union

from onta \
    import world
from onta.actuality \
    import state, conf
from onta.concretion import taxonomy
from onta.concretion.facticity \
    import formulae
from onta.metaphysics \
    import logger, settings, device
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
    ) -> tuple:
        return tuple(
            ( 
                key, 
                value 
            ) 
            if value else
            ( 
                key , 
                None
            )
            for key, value 
            in slot_configuration.items()
        )


    @staticmethod
    def immute_armory_size(
        avatar_configuration
    ) -> tuple:
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
    ) -> tuple:
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

    @staticmethod 
    def immute_pack_pieces(
        pack_piece_configuration
    ) -> tuple:
        return tuple(
            (
                pack_piece.size.w, 
                pack_piece.size.h
            ) 
            for pack_piece 
            in list(
                pack_piece_configuration.values()
            )
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
        self.properties = configure.apriori.properties
        self.styles = configure.apriori.styles.get(self.media_size)

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
            self.styles.get(
                taxonomy.QualiaPartitions.PACK.value
            ).margins.w, 
            self.styles.get(
                taxonomy.QualiaPartitions.PACK.value
            ).margins.h
        )
        pack_alignment = (
            self.styles.get(
                taxonomy.QualiaPartitions.PACK.value
            ).alignment.horizontal,
            self.styles.get(
                taxonomy.QualiaPartitions.PACK.value
            ).alignment.vertical
        )
        horizontal_alignment = pack_alignment[0]

        bag_piece_sizes = self.immute_pack_pieces(
            self.quale_conf.get(
                taxonomy.QualiaFamilies.PIECEWISE.value
            ).get(
                taxonomy.QualiaType.BAG.value
            )
        )

        belt_piece_sizes = self.immute_pack_pieces(
            self.quale_conf.get(
                taxonomy.QualiaFamilies.PIECEWISE.value
            ).get(
                taxonomy.QualiaType.BELT.value
            )
        )

        bag_dim = self.get_dimensions(
            taxonomy.QualiaType.BAG.value
        )

        belt_dim = self.get_dimensions(
            taxonomy.QualiaType.BELT.value
        )

        wallet_dim = self.get_dimensions(
            taxonomy.QualiaType.WALLET.value
        )

        setattr(
            self.render_points,
            taxonomy.QualiaType.BAG.value,
            formulae.bag_coordinates(
                bag_piece_sizes,
                bag_dim,
                pack_alignment,
                pack_margins,
                player_device.dimensions,
            )
        )

        bag_initial_render_pt = self.render_points.get(
            taxonomy.QualiaType.BAG.value
        )[0]

        setattr(
            self.render_points,
            taxonomy.QualiaType.BELT.value,
            formulae.belt_coordinates(
                bag_initial_render_pt,
                belt_piece_sizes,
                belt_dim,
                horizontal_alignment,
                pack_margins,
                bag_dim,
                bag_dim
            )
        )

        belt_initial_render_pt = self.render_points.get(
            taxonomy.QualiaType.BELT.value
        )[0]

        setattr(
            self.render_points,
            taxonomy.QualiaType.WALLET.value,
            formulae.wallet_coordinates(
                belt_initial_render_pt,
                bag_initial_render_pt,
                bag_dim,
                belt_dim,
                wallet_dim,
                horizontal_alignment,
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

        mirror_alignment = (
            self.styles.get(
                taxonomy.QualiaType.MIRROR.value
            ).alignment.horizontal,
            self.styles.get(
                taxonomy.QualiaType.MIRROR.value
            ).alignment.vertical
        )

        mirror_rank = (
            self.properties.mirror.columns,
            self.properties.mirror.rows,
        )

        # NOTE: dependent on 'unit' and 'empty' being the same dimensions...
        mirror_dim = (
            self.quale_conf.get(
                taxonomy.QualiaFamilies.STATEFUL.value
            ).get(
                taxonomy.QualiaType.MIRROR.value
            ).get(
                taxonomy.Measure.UNIT.value
            ).size.w,
            self.quale_conf.get(
                taxonomy.QualiaFamilies.STATEFUL.value
            ).get(
                taxonomy.QualiaType.MIRROR.value
            ).get(
                taxonomy.Measure.UNIT.value
            ).size.h
        )

        margins= (
            self.styles.get(
                taxonomy.QualiaType.MIRROR.value
            ).margins.w * player_device.dimensions[0],
            self.styles.get(
                taxonomy.QualiaType.MIRROR.value
            ).margins.h * player_device.dimensions[1]
        )

        padding = (
            self.styles.get(
                taxonomy.QualiaType.MIRROR.value
            ).padding.w,
            self.styles.get(
                taxonomy.QualiaType.MIRROR.value
            ).padding.h
        )

        mirror_stack = self.styles.get(
            taxonomy.QualiaType.MIRROR.value
        ).stack

        device_dim = player_device.dimensions
        
        setattr(
            self.render_points,
            taxonomy.QualiaType.MIRROR.value,
            formulae.mirror_coordinates(
                device_dim,
                mirror_alignment,
                mirror_stack,
                margins,
                padding,
                mirror_rank,
                mirror_dim
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

        alignment = (
            self.styles.get(
                taxonomy.QualiaType.SLOT.value
            ).alignment.horizontal,
            self.styles.get(
                taxonomy.QualiaType.SLOT.value
            ).alignment.vertical
        )
        margins = (
            self.styles.get(
                taxonomy.QualiaType.SLOT.value
            ).margins.w,
            self.styles.get(
                taxonomy.QualiaType.SLOT.value
            ).margins.h
        )

        cap_dim = formulae.rotate_dimensions(
            (
                self.quale_conf.get(
                    taxonomy.QualiaFamilies.ROTATABLE.value
                ).get(
                    taxonomy.QualiaType.CAP.value
                ).size.w,
                self.quale_conf.get(
                    taxonomy.QualiaFamilies.ROTATABLE.value
                ).get(
                    taxonomy.QualiaType.CAP.value
                ).size.h
            ),
            self.quale_conf.get(
                taxonomy.QualiaFamilies.ROTATABLE.value
            ).get(
                taxonomy.QualiaType.CAP.value
            ).definition,
            self.styles.get(
                taxonomy.QualiaType.SLOT.value
            ).stack
        )

        buffer_dim = formulae.rotate_dimensions(
            (
                self.quale_conf.get(
                    taxonomy.QualiaFamilies.ROTATABLE.value
                ).get(
                    taxonomy.QualiaType.BUFFER.value
                ).size.w,
                self.quale_conf.get(
                    taxonomy.QualiaFamilies.ROTATABLE.value
                ).get(
                    taxonomy.QualiaType.BUFFER.value
                ).size.h
            ),
            self.quale_conf.get(
                taxonomy.QualiaFamilies.ROTATABLE.value
            ).get(
                taxonomy.QualiaType.BUFFER.value
            ).definition,
            self.styles.get(
                taxonomy.QualiaType.SLOT.value
            ).stack
        )

        slot_dim = (
            self.quale_conf.get(
                taxonomy.QualiaFamilies.STATEFUL.value
            ).get(
                taxonomy.QualiaType.SLOT.value
            ).disabled.size.w,
            self.quale_conf.get(
                taxonomy.QualiaFamilies.STATEFUL.value
            ).get(
                taxonomy.QualiaType.SLOT.value
            ).disabled.size.h
        )

        slot_total = self.properties.get(
            taxonomy.QualiaType.SLOT.value
        ).total

        slot_stack = self.styles.get(
            taxonomy.QualiaType.SLOT.value
        ).stack

        device_dim = player_device.dimensions
        setattr(
            self.render_points,
            taxonomy.QualiaType.SLOT.value,
            formulae.slot_coordinates(
                slot_total,
                slot_dim,
                buffer_dim,
                cap_dim,
                device_dim,
                alignment,
                margins,
                slot_stack,
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
            taxonomy.QualiaType.SLOT.value,
            state_ao.get_state('dynamic').hero.get(
                taxonomy.SpriteProperty.SLOT.value
            )
        )
        setattr(
            self.containers,
            taxonomy.AvatarType.EQUIPMENT.value,
            state_ao.get_state('dynamic').hero.get(
                taxonomy.SpriteProperty.CAPITAL.value
            ).get(
                taxonomy.CapitalProperty.EQUIPMENT.value
            )
        )
        setattr(
            self.containers,
            taxonomy.QualiaPartitions.PACK.value,
            state_ao.get_state('dynamic').hero.get(
                taxonomy.SpriteProperty.PACK.value
            )
        )
        setattr(
            self.containers,
            taxonomy.QualiaPartitions.MEASURE.value,
            munch.Munch({
                taxonomy.QualiaType.MIRROR.value: 
                    state_ao.get_state('dynamic').hero.get(
                        taxonomy.SpriteProperty.HEALTH.value
                    )
            })
        )

        self._calculate_slot_frame_map()
        self._calculate_mirror_frame_map()

        for pack_key in list(
            e.value 
            for e
            in taxonomy.PackQualiaPartition.__members__.values()
        ):
            self._calculate_pack_piece_map(pack_key)
            


    def _calculate_avatar_positions(
        self
    ) -> None:
        """Calculate each _Slot_, _Pack_ and _Wallet_ avatar positions
        """
        # NOTE: this ugliness is all in service of immutability...
        immuted_slots = ExtrinsicQuale.immute_slots(
            self.containers.get(
                taxonomy.QualiaType.SLOT.value
            )
        )

        immuted_arms = ExtrinsicQuale.immute_armory_size(
            self.avatar_conf
        )

        immuted_inventory = ExtrinsicQuale.immute_inventory_size(
            self.avatar_conf
        )

        slot_render_points = tuple(
            self.render_points.get(
                taxonomy.QualiaType.SLOT.value
            )
        )

        bag_render_points = tuple(
            self.render_points.get(
                taxonomy.QualiaType.BAG.value
            )
        )

        belt_render_points = tuple(
            self.render_points.get(
                taxonomy.QualiaType.BELT.value
            )
        )

        slot_maps = tuple(
            self.properties.get(
                taxonomy.QualiaType.SLOT.value
            ).maps
        )

        # TODO: must be a better way to calculate this...
        slot_avatar_indices = tuple( 
            (
                slot_state, 
                slot_index
            ) 
            for slot_state, slot_index
            in zip( 
                [ 'cast', 'thrust', 'shoot', 'slash' ], 
                [ 1, 3, 5, 7 ]
            )
        )

        bag = self.containers.get(
            taxonomy.QualiaPartitions.PACK.value
        ).get(
            taxonomy.QualiaType.BAG.value
        )

        belt = self.containers.get(
            taxonomy.QualiaPartitions.PACK.value
        ).get(
            taxonomy.QualiaType.BELT.value
        )

        slot_dim = self.get_dimensions(
            taxonomy.QualiaType.SLOT.value
        )

        bag_dim = self.get_dimensions(
            taxonomy.QualiaType.BAG.value
        )

        belt_dim = self.get_dimensions(
            taxonomy.QualiaType.BELT.value
        )

        setattr(
            self.render_points,
            taxonomy.SelfType.AVATAR.value,
            formulae.slot_avatar_coordinates(
                immuted_slots, 
                immuted_arms,
                immuted_inventory,
                slot_render_points,
                bag_render_points,
                belt_render_points,
                slot_maps,
                slot_avatar_indices, 
                bag,
                belt, 
                slot_dim,
                bag_dim,
                belt_dim,
            )
        )

        setattr(
            self.frame_maps, 
            taxonomy.SelfType.AVATAR.value, 
            munch.Munch({})
        )

        for i, _ in enumerate(
            self.render_points.get(
                taxonomy.SelfType.AVATAR.value
            )
        ):
            if i < len(
                self.properties.get(
                    taxonomy.QualiaType.SLOT.value
                ).maps
            ):
                slot_mapping = self.properties.get(
                    taxonomy.QualiaType.SLOT.value
                ).maps[i]

                container_slot = self.containers.get(
                    taxonomy.QualiaType.SLOT.value
                ).get(slot_mapping)

                setattr(
                    self.frame_maps.get(
                        taxonomy.SelfType.AVATAR.value
                    ), 
                    str(i), 
                    container_slot
                )

        bag_avatar_mapping = str(
            len(
                self.frame_maps.get(
                    taxonomy.SelfType.AVATAR.value
                )
            )
        )

        bag_contents = self.containers.get(
            taxonomy.QualiaPartitions.PACK.value
        ).get(
            taxonomy.QualiaType.BAG.value
        )

        setattr(
            self.frame_maps.get(
                taxonomy.SelfType.AVATAR.value
            ),
            bag_avatar_mapping,
            bag_contents
        )

        belt_avatar_mapping = str(
            len(
                self.frame_maps.get(
                    taxonomy.SelfType.AVATAR.value
                )
            )
        )
        
        belt_contents = self.containers.get(
            taxonomy.QualiaPartitions.PACK.value
        ).get(
            taxonomy.QualiaType.BELT.value
        )

        setattr(
            self.frame_maps.get(
                taxonomy.SelfType.AVATAR.value
            ),
            belt_avatar_mapping,
            belt_contents
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
            taxonomy.QualiaType.SLOT.value,
            munch.Munch({
                key: taxonomy.Traversal.DISABLED.value
                if val is None 
                else taxonomy.Traversal.ENABLED.value
                for key, val 
                in self.containers.get(
                    taxonomy.QualiaType.SLOT.value
                ).items()
            })
        )


    def _calculate_mirror_frame_map(
        self, 
    ) -> dict:
        setattr(
            self.frame_maps,
            taxonomy.QualiaType.MIRROR.value,
            munch.Munch({
                i: taxonomy.Measure.UNIT.value
                if i <= self.containers.get(
                    taxonomy.QualiaPartitions.MEASURE.value  
                ).get(
                    taxonomy.QualiaType.MIRROR.value
                ).current - 1 
                else taxonomy.Measure.EMPTY.value
                for i in range(
                    self.properties.get(
                        taxonomy.QualiaType.MIRROR.value
                    ).bounds
                )
                if i <= self.containers.get(
                    taxonomy.QualiaPartitions.MEASURE.value
                ).get(
                    taxonomy.QualiaType.MIRROR.value
                ).max - 1
            })
        )


    def _calculate_pack_piece_map(
        self, 
        pack_key: str
    ) -> dict:
        if pack_key in [ 
            taxonomy.QualiaType.BAG.value, 
            taxonomy.QualiaType.BELT.value 
        ]:
            pack_piece_keys = list(
                self.quale_conf.get(
                    taxonomy.QualiaFamilies.PIECEWISE.value
                ).get(pack_key).keys()
            )

            setattr(
                self.frame_maps,
                pack_key,
                munch.Munch({
                    i: key 
                    for i, key 
                    in enumerate(pack_piece_keys)
                })
            )


    def _calculate_bag_dimensions(
        self
    ) -> tuple:
        if not self.dimensions.get(
            taxonomy.QualiaType.BAG.value
        ):
            bagset = self.quale_conf.get(
                taxonomy.QualiaFamilies.PIECEWISE.value
            ).get(
                taxonomy.QualiaType.BAG.value
            )

            total_bag_width = 0
            for bag_piece in bagset.values():
                total_bag_width += bag_piece.size.w

            # NOTE: dependent on both pieces being the same height
            # i.e., the pack sheet can only be broken in the 
            # horizontal direction
            total_bag_height = bagset.get(
                list(bagset.keys())[0]
            ).size.h

            bag_dim = ( 
                total_bag_width, 
                total_bag_height 
            )
            
            setattr(
                self.dimensions,
                taxonomy.QualiaType.BAG.value,
                bag_dim
            )
        return self.dimensions.bag


    def _calculate_belt_dimensions(
        self
    ) -> tuple:
        if not self.dimensions.get(
            taxonomy.QualiaType.BELT.value
        ):
            beltset = self.quale_conf.get(
                taxonomy.QualiaFamilies.PIECEWISE.value
            ).get(
                taxonomy.QualiaType.BELT.value
            )

            total_belt_width = 0
            for belt_piece in beltset.values():
                total_belt_width += belt_piece.size.w

            total_belt_height = beltset.get(
                list(
                    beltset.keys()
                )[0]
            ).size.h

            belt_dim = ( 
                total_belt_width, 
                total_belt_height 
            )

            setattr(
                self.dimensions,
                taxonomy.QualiaType.BELT.value,
                belt_dim
            )

        return self.dimensions.get(
            taxonomy.QualiaType.BELT.value
        )


    def _calculate_wallet_dimensions(
        self
    ) -> tuple:
        if not self.dimensions.get(
            taxonomy.QualiaType.WALLET.value
        ):
            wallet_dim = (
                self.quale_conf.get(
                    taxonomy.QualiaFamilies.SIMPLE.value
                ).get(
                    taxonomy.QualiaType.WALLET.value
                ).size.w, 
                self.quale_conf.get(
                    taxonomy.QualiaFamilies.SIMPLE.value
                ).get(
                    taxonomy.QualiaType.WALLET.value
                ).size.h
            )

            setattr(
                self.dimensions,
                taxonomy.QualiaType.WALLET.value,
                wallet_dim
            )

        return self.dimensions.get(
            taxonomy.QualiaType.WALLET.value
        )


    def _calculate_slot_dimensions(
        self
    ) -> tuple:
        if not self.dimensions.get(
            taxonomy.QualiaType.SLOT.value
        ):
            setattr(
                self.dimensions,
                taxonomy.QualiaType.SLOT.value,
                (
                    self.quale_conf.get(
                        taxonomy.QualiaFamilies.STATEFUL.value
                    ).get(
                        taxonomy.QualiaType.SLOT.value
                    ).get(
                        taxonomy.Traversal.ENABLED.value
                    ).size.w, 
                    self.quale_conf.get(
                        taxonomy.QualiaFamilies.STATEFUL.value
                    ).get(
                        taxonomy.QualiaType.SLOT.value
                    ).get(
                        taxonomy.Traversal.ENABLED.value
                    ).size.h
                )
            )
        return self.dimensions.get(
            taxonomy.QualiaType.SLOT.value
        )

    def get_dimensions(
        self,
        quale_key
    ) -> tuple:
        if quale_key == taxonomy.QualiaType.SLOT.value:
            return self._calculate_slot_dimensions()
        if quale_key == taxonomy.QualiaType.WALLET.value:
            return self._calculate_wallet_dimensions()
        if quale_key == taxonomy.QualiaType.BAG.value:
            return self._calculate_bag_dimensions()
        if quale_key == taxonomy.QualiaType.BELT.value:
            return self._calculate_belt_dimensions()
        raise KeyError(
            f'{quale_key} is not a valid ExtrinsicQuale component'
        )

    def get_frame_map(
        self, 
        component_key: str
    ) -> munch.Munch:
        return self.frame_maps.get(component_key)


    def get_cap_directions(
        self
    ) -> str:
        if self.styles.get(
            taxonomy.QualiaType.SLOT.value
        ).stack == 'horizontal':
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
        return self.styles.get(
            taxonomy.QualiaType.SLOT.value
        ).stack

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

        # Update Slots
        if self.containers.get(
            taxonomy.QualiaType.SLOT.value
        ) != game_world.hero.get(
            taxonomy.QualiaType.SLOT.value
        ):

            hero_slots = game_world.hero.get(
                taxonomy.QualiaType.SLOT.value
            ).copy()

            setattr(
                self.containers,
                taxonomy.QualiaType.SLOT.value,
                hero_slots
            )
            self._calculate_slot_frame_map()
            avatar_touched = True

        # Update Mirror
        if self.containers.get(
            taxonomy.QualiaPartitions.MEASURE.value
        ).get(
            taxonomy.QualiaType.MIRROR.value
        )!= game_world.hero.health:
            hero_health = game_world.hero.health.copy()
            setattr(
                self.containers.get(
                    taxonomy.QualiaPartitions.MEASURE.value
                ), 
                taxonomy.QualiaType.MIRROR.value, 
                hero_health
            )
            self._calculate_mirror_frame_map()

        # Update Pack
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
