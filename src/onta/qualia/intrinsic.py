from typing import Union
import munch

from onta \
    import world
from onta.actuality \
    import state
from onta.concretion import taxonomy
from onta.concretion.facticity \
    import formulae
from onta.metaphysics \
    import device, logger, settings
from onta.qualia \
    import apriori
from onta.qualia.quale \
    import Quale
from onta.qualia.thoughts \
    import bauble, symbol

log = logger.Logger(
    'onta.qualia.intrinsic', 
    settings.LOG_LEVEL
)

BAUBLE_THOUGHTS = [ 
    'armory', 
    'equipment', 
    'inventory' 
]
SYMBOL_THOUGHTS = [ 
    'map', 
    'status'
]

class IntrinsicQuale(Quale):
    """
    
    A `IntrinsicQuale` is essentially an in-game menu; it composed of "ideas", i.e. buttons, the player iterates throguh and then executes. These "ideas" become "thoughts", i.e. submenus, when executed. When an "idea" is executed, focus is shifted to the "thought" until the player pops back into the "idea" selection menu.
    """

    def __init__(
        self, 
        player_device: device.Device, 
        ontology_path: str = settings.DEFAULT_DIR
    ) -> None:
        super().__init__(
            player_device, 
            ontology_path
        )
        state_ao = state.State(ontology_path)
        self._init_fields()
        self.media_size = apriori.find_media_size(
            player_device.dimensions, 
            self.sizes, 
            self.breakpoints
        )
        self._init_idea_positions(player_device)
        self._init_thoughts(
            player_device,
            state_ao
        )
        self._init_ideas(state_ao)

    def _init_fields(
        self
    ):
        """
        .. note::
            ```python
            self.thoughts = {
                'thought_1': {
                    # ...
                },
                # ...
            }
            self.ideas = {
                'thought_1': {
                    'left': 'enabled',
                    'middle': 'enabled',
                    'right': 'enabled'
                },
                # ...
            }
            ```
        """
        self.thoughts = munch.Munch({})
        self.ideas = munch.Munch({})
        self.idea_rendering_points = []
        self.idea_frame_map = []
        self.idea_piece_map = []
        self.active_idea = None
        self.active_thought = None
        self.quale_activated = False
        self.media_size = None
        self.alpha = None
      

        self.theme = tuple(
            self.theme.get(
                taxonomy.Theme.INTRINSIC.value
            ).get(
                channel.value
            )
            for channel
            in taxonomy.Channels.__members__.values()
        )


    def _init_idea_positions(
        self, 
        player_device: device.Device
    ) -> None:
        quale_margins = (
            self.styles.default.margins.w,
            self.styles.default.margins.h
        )
        quale_padding = (
            self.styles.default.padding.w,
            self.styles.default.padding.h
        )

        # NOTE: all idea component pieces have the same dim, so any will do...
        # NOTE: ideas are "thought" buttons
        # [ (left_w, left_h), (middle_w, middle_h), (right_w, right_h) ]
        dims = [
            ( 
                self.quale_conf.piecewise_stateful.idea.enabled.get(piece).size.w, 
                self.quale_conf.piecewise_stateful.idea.enabled.get(piece).size.h 
            ) 
            for piece in list(
                self.quale_conf.piecewise_stateful.idea.enabled.keys()
            )
        ]

        num_ideas = len(self.thought_conf)

        num_pieces = len(self.quale_conf.piecewise_stateful.idea.enabled)

        device_dim = player_device.dimensions

        stack_style = self.styles.default.stack

        self.idea_rendering_points = formulae.idea_coordinates(
            dims,
            num_ideas,
            num_pieces,
            device_dim,
            stack_style,
            quale_margins,
            quale_padding
        )


    def _init_thoughts(
        self,
        player_device: device.Device,
        state_ao: state.State
    ):
        components_conf = munch.Munch({
            taxonomy.QualiaType.BAUBLE.value: 
                self.quale_conf.get(
                    taxonomy.QualiaFamilies.PIECEWISE_STATEFUL.value
                ).get(
                    taxonomy.QualiaType.BAUBLE.value
                ),
            taxonomy.QualiaType.CONCEPT.value: 
                self.quale_conf.get(
                    taxonomy.QualiaFamilies.SIMPLE.value
                ).get(
                    taxonomy.QualiaType.CONCEPT.value
                ),
            taxonomy.QualiaType.CONCEPTION.value: 
                self.quale_conf.get(
                    taxonomy.QualiaFamilies.SIMPLE.value
                ).get(
                    taxonomy.QualiaType.CONCEPTION.value
                )
        }) # TODO: this seems redundant ... ?

        piece_conf = self.quale_conf.get(
            taxonomy.QualiaFamilies.PIECEWISE_STATEFUL.value
        ).get(
            taxonomy.QualiaType.IDEA.value
        ).get(
            taxonomy.StatefulQualiaTraversal.ENABLED.value
        )

        piece_keys = list(
            piece_conf.keys()
        )

        full_width = sum(
            piece_conf.get(
                piece
            ).get(
                taxonomy.Measurement.SIZE.value
            ).get(
                taxonomy.Measurement.WIDTH.value
            )
            for piece 
            in piece_keys
        )

        full_height = piece_conf.get(
            piece_keys[0]
        ).get(
            taxonomy.Measurement.SIZE.value
        ).get(
            taxonomy.Measurement.HEIGHT.value
        )

        idea_dim = (
            full_width, 
            full_height
        )

        # (armory, armory_conf), (equipment, equipment_conf), ...
        for thought_key, thought_conf in self.thought_conf.items():
            log.debug(
                f'Creating {thought_key} thought...', 
                'IntrinsicQuale._init_thoughts'
            )
            
            if thought_key in BAUBLE_THOUGHTS:
                # TODO:? There is a redundancy here. the class itself knows which thoughts are baubles
                # through this constant, but the configuration data structure also passes in that information. 

                # this brings up the question. how much of the data should be in the configuration and how much
                # should be programmatic logic?

                setattr(
                    self.thoughts, 
                    thought_key,
                    bauble.BaubleThought(
                        thought_key,
                        thought_conf,
                        components_conf,
                        self.styles,
                        self.avatar_conf,
                        self.idea_rendering_points[0],
                        idea_dim,
                        player_device.dimensions,
                        state_ao,
                    )
                )

            elif thought_key in SYMBOL_THOUGHTS:
                    pass
                # TODO: this


    def _init_ideas(
        self, 
        state_ao: state.State
    ) -> None:
        """_summary_

        :param state_ao: _description_
        :type state_ao: state.State
        """
        # TODO: calculate based on state information

        # NOTE: this is what creates `self.thoughts`
        #       `self.thoughts`
        for i, name in enumerate(list(self.thought_conf.keys())):
            if i == 0:
                self._activate_idea(name)
                self.active_idea = i
                continue
            self._enable_idea(name)


    def _idea_pieces(
        self
    ) -> list:
        return list(
            self.quale_conf.get(
                taxonomy.QualiaFamilies.PIECEWISE_STATEFUL.value
            ).get(
                taxonomy.QualiaType.IDEA.value
            ).get(
                taxonomy.StatefulQualiaTraversal.ENABLED.value
            ).keys()
        )


    def _activate_idea(
        self, 
        idea_key: str
    ) -> None:
        """_summary_

        :param idea_key: _description_
        :type idea_key: str
        """
        setattr(
            self.ideas,
            idea_key,
            munch.Munch({
                piece: taxonomy.StatefulQualiaTraversal.ACTIVE.value
                for piece 
                in self._idea_pieces()
            })
        )


    def _disable_idea(
        self, 
        idea_key: str
    ) -> None:
        """_summary_

        :param idea_key: _description_
        :type idea_key: str
        """
        setattr(
            self.ideas,
            idea_key,
            munch.Munch({
                piece: taxonomy.StatefulQualiaTraversal.DISABLED.value
                for piece 
                in self._idea_pieces()
            })
        )


    def _enable_idea(
        self, 
        idea_key: str
    ) -> None:
        """_summary_

        :param idea_key: _description_
        :type idea_key: str
        """
        setattr(
            self.ideas,
            idea_key,
            munch.Munch({
                piece: taxonomy.StatefulQualiaTraversal.ENABLED.value
                for piece 
                in self._idea_pieces()
            })
        )


    def _increment_idea(
        self
    ) -> None:
        """_summary_
        """
        idea_list = list(self.thoughts.keys())
        ## TODO: skip disabled idea buttons
        previous_active = self.active_idea
        self.active_idea -= 1

        if self.active_idea < 0:
            self.active_idea = len(idea_list) - 1
        
        self._enable_idea(
            idea_list[previous_active]
        )
        self._activate_idea(
            idea_list[self.active_idea]
        )


    def _decrement_idea(
        self
    ) -> None:
        """_summary_
        """
        idea_list = list(self.thoughts.keys())
        ## TODO: skip disabled buttons
        previous_active = self.active_idea
        self.active_idea += 1

        if self.active_idea > len(idea_list) - 1:
            self.active_idea = 0
        
        self._enable_idea(
            idea_list[previous_active]
        )
        self._activate_idea(
            idea_list[self.active_idea]
        )


    def _ideate(
        self,
    ) -> None:
        activate_thought_key = list(
            self.thoughts.keys()
        )[self.active_idea]
        self.active_thought = self.thoughts.get(
            activate_thought_key
        )


    def _forget(
        self,
    ) -> None:
        self.active_thought = None


    def _calculate_idea_frame_map(
        self
    ) -> list:
        # NOTE **: frame changes ..
        self.idea_frame_map = [] 
        for piece_conf in self.ideas.values():
            for piece_state in piece_conf.values():
                self.idea_frame_map.append(piece_state)
        return self.idea_frame_map


    def _calculate_idea_piece_map(
        self
    ) -> list:
        # NOTE **: ...but pieces stay the same ...
        if not self.idea_piece_map:
            for piece_conf in self.ideas.values():
                for piece_key in piece_conf.keys():
                    self.idea_piece_map.append(piece_key)
        return self.idea_piece_map


    def _active_thought_key(
        self
    ) -> str:
        return list(
            self.thoughts.keys()
        )[self.active_idea]


    def get_active_thought(
        self
    ) -> Union[
        bauble.BaubleThought,
        symbol.SymbolThought
    ]:
        return self.thoughts.get(
            self._active_thought_key()
        )


    def idea_maps(
        self
    ) -> tuple:
        return (
            self._calculate_idea_frame_map(), 
            self._calculate_idea_piece_map()
        )


    def toggle_quale(
        self
    ) -> None:
        self.quale_activated = not self.quale_activated


    def rendering_points(
        self, 
        interface_key: str
    ) -> list:
        if interface_key == taxonomy.QualiaType.IDEA.value:
            return self.idea_rendering_points


    def update(
        self, 
        quale_input: Union[
            munch.Munch,
            None
        ],
        game_world: world.World
    ) -> None:
        if quale_input:
            
            if quale_input.arise:
                self.toggle_quale()
                return

            # controls when traversing main button stack
            if self.active_thought is None:
                if quale_input.increment:
                    self._increment_idea()

                elif quale_input.decrement:
                    self._decrement_idea()

                elif quale_input.execute:
                    self._ideate()

                return

            if quale_input.reconsider:
                self._forget()
                return

            # controls when traversing tab stacks
            if isinstance(
                self.active_thought, 
                bauble.BaubleThought
            ):

                if quale_input.increment:
                    self.active_thought.increment_bauble_row()

                elif quale_input.decrement:
                    self.active_thought.decrement_bauble_row()

                elif quale_input.traverse:
                    self.active_thought.increment_bauble_selection()

                elif quale_input.reverse:
                    self.active_thought.decrement_bauble_selection()

                elif quale_input.execute:
                    selection = self.active_thought.select()
                    return selection
                    
                self.active_thought.update(game_world)
                return

            elif isinstance(
                self.active_thought, 
                symbol.SymbolThought
            ):
                pass