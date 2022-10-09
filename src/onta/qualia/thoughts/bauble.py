
import munch
from typing \
    import Union

from onta \
    import world
from onta.actuality \
    import state
from onta.concretion import taxonomy
from onta.concretion.facticity \
    import formulae
from onta.metaphysics \
    import settings, logger

log = logger.Logger(
    'onta.qualia.thoughts.bauble', 
    settings.LOG_LEVEL
)

class BaubleThought():
    """ A `BaubleThought` is a traversible menu. It contains rows of "baubles". Each bauble is a collection of slots mapped to a concept. A concept represents a division of player state information. For instance, a "slash" concept maps to a bauble of slots that contain all the weapons a player can equip in the "slash" slot. Each concept has a "conception" map that contains the currently selected slot to its equipment; the "conception" is the piece of equipment currently equipped to the player.

    A bauble row can be visualized as:

        concept  |  conception | bauble[slots]
    
    E.g.,

        slash    |   short_sword  |  [short_sword, knife, axe]
    
    Represent a row mapped to the "slash" concept with a "shortsword" currently equipped, i.e. "conceptualized", with the array of selections "[short_sword, knife, axe]" representing a traversible array of equipment the player can equip. For example, if the player traverses over the bauble and selects "knife", the "conception" will switch to "knife", and this information will propagate up through the menu, into the game world, where the player will equip the "knife" in-game.
    """

    def __init__(
        self, 
        name: str,
        components: munch.Munch, 
        components_conf: munch.Munch,
        styles: munch.Munch, 
        avatar_conf: munch.Munch,
        alignment_reference: tuple,
        device_dim: tuple,
        state_ao: state.State
    ) -> None: 
        """_summary_

        :param name: Name of the `BaubleThought`. Used purely for logging. Does not materially affect the class in anyway.
        :type name: str
        :param components: This parameter corresponds to the array of_(component, label)_ tuples in the _conf/self/qualia.yml_ underneath the `thoughts` property. This array configures how many bauble rows are displayed; the labels determine the mapping between the bauble row and the player _Capital_ component.
        :type components: list
        :param components_conf: This parameter corresponds to the map of _Qualia_ pieces, states and their sizes in _conf/self/qualia.yml_.
        :type components_conf: munch.Munch
        :param styles: _description_
        :type styles: munch.Munch
        :param avatar_conf: _description_
        :type avatar_conf: munch.Munch
        :param alignment_reference: The point on the canvas 
        :type alignment_reference: tuple
        :param alignment_dim: _description_
        :type alignment_dim: tuple
        :param device_dim: _description_
        :type device_dim: tuple
        :param state_ao: _description_
        :type state_ao: state.State
        """
        self.name = name
        self.components = components
        self.components_conf = components_conf
        self.avatar_conf = avatar_conf
        self.styles = styles
        self.alignment_ref = alignment_reference
        self.device_dim = device_dim

        self._init_fields()
        
        self._init_components(
            state_ao.get_state('dynamic').get('hero').get('capital')
        )


    def _init_fields(
        self
    ) -> None:
        """Initialize class fields.

        .. note::
            ```python
            # E.g., If self.name == 'armory'
            self.baubles = {
                'slash': 'slash_avatar_key',
                'shoot': 'shoot_avatar_key',
                'thrust': 'thrust_avatar_key',
                'cast': 'cast_avatar_key'
            }

            ```
        """
        self.selected_row = 0

        self.baubles = munch.Munch({})

        self.bauble_render_points = []
        self.bauble_avatar_render_points = []
        self.bauble_frame_map = []
        self.bauble_piece_map = []
        self.bauble_avatar_map = []
        self.bauble_scroll_num = None

        self.concept_render_points = []

        self.conception_render_points = []
        self.conception_frame_map = []
        # NOTE: can get conception avatars through `self.baubles`
        self.conception_avatar_map = []


    def _init_components(
        self,
        player_capital: munch.Munch
    ) -> None:
        """_summary_

        :param player_capital: _description_
        :type player_capital: munch.Munch

        .. note::
            The label of a bauble (different than its content in `self.baubles`; "label" refers to the `label` property in _conf/self/qualia.yml_!) must map to a possible label in a _Sprite_'s `capital`, i.e. `equipment[].label` must map to `armor`, `shield`, `bag` or `belt`, `armory[].label` must map to `slash`, `thrust`, `shoot` or `cast,  `inventory etc.
        .. note::
            In other words, the possible values of `component.label` are `armor | shield | thrust | shoot | slash | cast | bag | belt`. TODO: there will probably be more to add here.
        """
        if not self.components:
            return

        log.debug(
            f'Initializing {self.name} thought...', 
            'BaubleThought._init_components'
        )
        
        for component in self.components:
            if not component:
                continue

            log.debug(
                f'Initializing {component.label} {component.component}', 
                'BaubleThought._init_components'
            )


            # NOTE: bauble-based thought label must correspond to the component label of the player capital they operate on. See first note in docstring.
            iter_set = player_capital.get(self.name)

            component_avatars = [
                arm.component 
                for arm 
                in iter_set
                if arm.label == component.label
            ]

            setattr(
                self.baubles, 
                component.label, 
                munch.Munch({
                    'selectable': component_avatars,
                    'selected': None,
                })
            )

        
        if len(self.baubles) > 0:
            self._calculate_conceptual_positions()
            self._calculate_bauble_positions()
            self._calculate_bauble_avatar_positions()
            self._calculate_bauble_frame_map()
            self._calculate_bauble_avatar_map()
            self.increment_bauble_selection()     


    def _update_components(
        self,
        player_capital: munch.Munch
    ) -> None:
        pass

    def _calculate_conceptual_positions(
        self
    ) -> None:
        if self.concept_render_points:
            return

        log.debug(
            f'Initialzing {self.name} concept and conception positions',
            'BaubleThought._calculate_conceptual_positions'
        )

        concept_styles = self.styles.get(
            taxonomy.QualiaType.CONCEPT.value
        )

        concept_margins = concept_styles.get(
            taxonomy.Style.MARGINS.value
        )
        concept_padding = concept_styles.get(
            taxonomy.Style.PADDING.value
        )
        concept_stack = concept_styles.get(
            taxonomy.Style.STACK.value
        )

        concept_conf = self.components_conf.get(
            taxonomy.QualiaType.CONCEPT.value
        ).get(
            taxonomy.StatefulQualiaTraversal.ENABLED.value
        )

        concept_dim = (
            concept_conf.get(
                taxonomy.Measurement.SIZE.value
            ).get(
                taxonomy.Measurement.WIDTH.value
            ),
            concept_conf.get(
                taxonomy.Measurement.SIZE.value
            ).get(
                taxonomy.Measurement.HEIGHT.value
            )
        )

        concept_num = len(self.baubles)


    def _calculate_concept_avatar_position(
        self
    ) -> None:
        pass


    def _calculate_bauble_positions(
        self,
    ) -> None:
        """_summary_

        .. note::
            Method is dependent on all baubles being the same height. Widths are free to vary. In other words, the baubles are constructed from horizontal pieces only. They cannot be broken up vertically.
        .. note::
            Starting points are dependent on stack style, but the baubles are always organized into rows.
        .. note::
            `piece_map` is static. It only needs calculated once, since bauble pieces are always rendered at the same location. However, the `frame_map` and `avatar_map` need recalculated on changes to the player static. In other words, the `piece_map` is calculated within this method, whereas the other maps are calculated in specialized methods that use state information from the _World_.
        """
        if self.bauble_render_points:
            return

        log.debug(
            f'Initializing {self.name} bauble positions', 
            'BaubleThought._calculate_bauble_positions'
        )

        # NOTE: Define function-scoped variables
        styles = self.styles.get(
            taxonomy.QualiaType.BAUBLE.value
        )
        raw_margins = styles.get(
            taxonomy.Style.MARGINS.value
        )
        raw_padding = styles.get(
            taxonomy.Style.PADDING.value
        )
        bauble_stack = styles.get(
            taxonomy.Style.STACK.value
        )
        bauble_conf = self.components_conf.get(
            taxonomy.QualiaType.BAUBLE.value
        ).get(
            taxonomy.StatefulQualiaTraversal.ENABLED.value
        )
        bauble_piece_widths = tuple(
            piece.get(
                taxonomy.Measurement.SIZE.value
            ).get(
                taxonomy.Measurement.WIDTH.value
            )
            for piece 
            in bauble_conf.values() 
        )
        # NOTE: here is where the height assumption is made. See note in docstring.
        bauble_height = bauble_conf.get(
            taxonomy.QualiaPiece.LEFT.value
        ).get(
            taxonomy.Measurement.SIZE.value
        ).get(
            taxonomy.Measurement.HEIGHT.value
        )
        bauble_padding = (
            self.device_dim[0] * raw_padding.get(
                taxonomy.Measurement.WIDTH.value
            ),
            self.device_dim[1] * raw_padding.get(
                taxonomy.Measurement.HEIGHT.value
            )
        )
        bauble_margins = (
            self.device_dim[0] * raw_margins.get(
                taxonomy.Measurement.WIDTH.value
            ),
            self.device_dim[1] * raw_margins.get(
                taxonomy.Measurement.HEIGHT.value
            )
        )

        bauble_num = len(self.baubles)

        # TODO: need to account for position of concepts and conceptions

        # NOTE: there is a bit of redundancy here, sice bauble_coordinates calls bauble_canvas. It might make sense to subsume the piece map into the canvas method...?
        self.bauble_scroll_num = formulae.bauble_canvas(
            bauble_height,
            bauble_piece_widths,
            bauble_padding,
            bauble_stack,
            self.alignment_ref,
            self.device_dim,
        )[-1]

        self.bauble_render_points = formulae.bauble_coordinates(
            bauble_num,
            bauble_height,
            bauble_piece_widths,
            bauble_margins,
            bauble_padding,
            bauble_stack,
            self.device_dim,
            self.alignment_ref,
        )

        self.bauble_piece_map = formulae.bauble_pieces(
            bauble_num,
            self.bauble_scroll_num
        )


    def _calculate_bauble_avatar_positions(
        self
    ) -> None:
        log.debug(
            f'Calcuating {self.name} bauble avatar positions', 
            'Thought._calculate_bauble_avatar_positions'
        )
        bauble_piece_widths = [ 
            piece.size.w 
            for piece 
            in self.components_conf.bauble.enabled.values() 
        ]
        total_bauble_width = sum(bauble_piece_widths)
            # NOTE: here is where the height assumption is made. See note in docstring.
        bauble_height = self.components_conf.bauble.enabled.left.size.h
            # NOTE: bauble pieces have diferent widths, so this will result in a small misalignment
            #       
        bauble_width = self.components_conf.bauble.enabled.left.size.w


        # TODO: this loop -> candidate for cython formulae module

        for bauble_label, bauble_conf in self.baubles.items():
            row = list(
                filter(
                    lambda x: x.label == bauble_label, 
                    self.components
                )
            ).pop()

            row_index = self.components.index(row)
            start_index = row_index * self.bauble_scroll_num
            start_point = self.bauble_render_points[start_index]
            added = 0

            for i, avatar_key in enumerate(bauble_conf.selectable):
                if avatar_key in list(self.avatar_conf.armory.keys()):
                    avatar_dim = (
                        self.avatar_conf.armory.get(avatar_key).size.w,
                        self.avatar_conf.armory.get(avatar_key).size.h
                    )
                elif avatar_key in list(self.avatar_conf.equipment.keys()):
                    avatar_dim = (
                        self.avatar_conf.equipment.get(avatar_key).size.w,
                        self.avatar_conf.equipment.get(avatar_key).size.h,
                    )
                elif avatar_key in list(self.avatar_conf.inventory.keys()):
                    avatar_dim = (
                        self.avatar_conf.inventory.get(avatar_key).size.w,
                        self.avatar_conf.inventory.get(avatar_key).size.h
                    )

                self.bauble_avatar_render_points.append(
                    (
                        start_point[0] + i * bauble_width + ( bauble_width - avatar_dim[0] )/2,
                        start_point[1] + ( bauble_height - avatar_dim[1] )/2
                    )
                )

                added += 1

                if added == self.bauble_scroll_num:
                    break
            
            while self.bauble_scroll_num > added:
                self.bauble_avatar_render_points.append(None)
                added += 1
     

    def _calculate_bauble_avatar_map(
        self
    ) -> None:
        self.bauble_avatar_map = []
        for bauble_conf in self.baubles.values():
            added = 0

            for avatar_key in bauble_conf.selectable:
                self.bauble_avatar_map.append(avatar_key)
                added += 1
                
                if added == self.bauble_scroll_num:
                    break

            while self.bauble_scroll_num > added:
                self.bauble_avatar_map.append(None)
                added += 1
 

    def _calculate_bauble_frame_map(
        self
    ) -> None:
        self.bauble_frame_map = []
        for bauble_conf in self.baubles.values():
            selected = bauble_conf.selected
            added = 0

            for avatar_key in bauble_conf.selectable:
                added += 1
                if avatar_key == selected:
                    self.bauble_frame_map.append(
                        taxonomy.StatefulQualiaTraversal.ACTIVE.value
                    )
                    continue

                self.bauble_frame_map.append(
                    taxonomy.StatefulQualiaTraversal.ENABLED.value
                )

                if added == self.bauble_scroll_num:
                    break

            while self.bauble_scroll_num > added:
                self.bauble_frame_map.append(
                    taxonomy.StatefulQualiaTraversal.DISABLED.value
                )
                added += 1


    def _deselect_bauble_row(   
        self
    ) -> None:
        row_key = list(self.baubles.keys())[self.selected_row]
        row_bauble = self.baubles.get(row_key)
        setattr(
            row_bauble,
            'selected',
            None
        )


    def _incrementable(
        self
    ) -> bool:
        return any(
            len(bauble.selectable) > 0 
            for bauble 
            in self.baubles.values()
        )


    def map_avatar_to_set(
        self, 
        avatar_key:str
    ) -> Union[str, None]:
        for avatarset_key,avatarset_conf in self.avatar_conf.items():
            if avatar_key in list(avatarset_conf.keys()):
                return avatarset_key
        return None


    def bauble_maps(
        self
    )-> tuple:
        return (
            self.bauble_frame_map, 
            self.bauble_piece_map, 
            self.bauble_avatar_map
        )


    def rendering_points(
        self,
        component_key: str
    ) -> Union[tuple, None]:
        if component_key == taxonomy.QualiaType.BAUBLE.value:
            return (
                self.bauble_render_points, 
                self.bauble_avatar_render_points
            )
        return None


    # TODO: what if more avatars than on-screen baubles?
    def increment_bauble_selection(
        self,
    ) -> None:
        if not self._incrementable():
            return 
        
        row_key = list(self.baubles.keys())[self.selected_row]
        row_bauble = self.baubles.get(row_key)

        if len(row_bauble.selectable) > 0:
            log.debug(
                'Incrementing bauble selection...', 
                'increment_bauble_selection'
            )

            if not row_bauble.selected:
                
                setattr(
                    row_bauble,
                    'selected',
                    row_bauble.selectable[0]
                )
                log.debug(
                    f'Current selection {row_bauble.selected}', 
                    'increment_bauble_selection'
                )
                return

            current_index = row_bauble.selectable.index(row_bauble.selected)
            current_index += 1
            if current_index > len(row_bauble.selectable) - 1:
                current_index = 0 

            setattr(
                row_bauble,
                'selected',
                row_bauble.selectable[current_index]

            )
            log.debug(
                f'Current selection {row_bauble.selected}', 
                'increment_bauble_selection'
            )


    def decrement_bauble_selection(
        self
    ) -> None:
        if not self._incrementable():
            return 

        row_key = list(self.baubles.keys())[self.selected_row]
        row_bauble = self.baubles.get(row_key)

        if len(row_bauble.selectable) > 0:
            log.debug(
                'Decrementing bauble selection...', 
                'decrement_bauble_selection'
            )

            if not row_bauble.selected:
                setattr(
                    row_bauble,
                    'selected',
                    row_bauble.selectable[-1]
                )
                log.debug(
                    f'Current selection {row_bauble.selected}', 
                    'decrement_bauble_selection'
                )
                return
            
            current_index = row_bauble.selectable.index(row_bauble.selected)
            current_index -= 1
            if current_index < 0:
                current_index = len(row_bauble.selectable) - 1
            setattr(
                row_bauble,
                'selected',
                row_bauble.selectable[current_index]
            )
            log.debug(
                f'Current selection {row_bauble.selected}', 
                'decrement_bauble_selection'
            )

        
    def decrement_bauble_row(
        self,
        select: bool = True,
        depth: int = 1
    ) -> None:
        if select:
            log.debug(
                'Deselecting current bauble row...', 
                'decrement_bauble_row'
            )
            self._deselect_bauble_row()
        else:
            log.debug(
                'Recursing through selectable rows...',
                'decrement_bauble_row'
            )

        # NOTE: avoid infinite recursion
        if depth >= len(self.baubles):
            return

        self.selected_row += 1
        if self.selected_row > len(self.baubles) - 1:
            self.selected_row = 0

        row_key = list(self.baubles.keys())[self.selected_row]
        row_bauble = self.baubles.get(row_key)

        if not row_bauble.selectable:
            self.decrement_bauble_row(False, depth + 1)

        if select:
            self.increment_bauble_selection()


    def increment_bauble_row(
        self,
        select: bool = True,
        depth: int = 1
    ) -> None:
        if select:
            log.debug(
                'Deselecting current bauble row...', 
                'increment_bauble_row'
            )
            self._deselect_bauble_row()
        else:
            log.debug(
                'Recursing through selectable rows...',
                'increment_bauble_row'
            )

        # NOTE: avoid infinite recursion
        if depth >= len(self.baubles):
            return

        self.selected_row -= 1
        if self.selected_row < 0:
            self.selected_row = len(self.baubles) - 1

        row_key = list(self.baubles.keys())[self.selected_row]
        row_bauble = self.baubles.get(row_key)

        # TODO: there is an infinite recursion here if all baubles are empty...
        if not row_bauble.selectable:
            self.increment_bauble_row(False, depth + 1)

        if select:
            self.increment_bauble_selection()


    def select(
        self
    ) -> dict:
        row_key = list(self.baubles.keys())[self.selected_row]
        row_bauble = self.baubles.get(row_key)
        return munch.Munch({
            'capital': self.name,
            'label': row_key,
            'selection': row_bauble.selected
        })


    def update(
        self,
        game_world: world.World
    ):
        self._update_components(
            game_world.hero.capital
        )
        self._calculate_bauble_frame_map()
        self._calculate_bauble_avatar_map()