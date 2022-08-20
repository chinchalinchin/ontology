
from typing import Union
import munch

import onta.settings as settings
import onta.loader.state as state
import onta.util.logger as logger 

log = logger.Logger('onta.engine.qualia.thought', settings.LOG_LEVEL)


# TODO: should enforce mutual exclusion between bauble type of thoughts and display type of thoughts.

# that way the render poiint methods don't need to worry about what type they are
#  generating render points for


class Thought():

    def __init__(
        self, 
        name: str,
        components: list, 
        components_conf: munch.Munch,
        styles: munch.Munch, 
        avatar_conf: munch.Munch,
        alignment_reference: tuple,
        alignment_dim: tuple,
        device_dim: tuple,
        state_ao: state.State
    ) -> None: 

        self.name = name
        self.components = components
        self.components_conf = components_conf
        self.avatar_conf = avatar_conf
        self.styles = styles
        self.alignment_ref = alignment_reference
        self.alignment_dim = alignment_dim
        self.device_dim = device_dim

        # Define in __init__ to avoid closure since tabs are created in loop by Menu
        self.baubles = munch.Munch({})
        self.bauble_render_points = []
        self.bauble_avatar_render_points = []
        self.bauble_frame_map = []
        self.bauble_piece_map = []
        self.bauble_avatar_map = []
        self.bauble_scroll_num = None

        self.asides = munch.Munch({})
        self.aside_render_points = []

        self.displays = munch.Munch({})
        self.display_render_points = []

        self.focii = munch.Munch({})
        self.focus_render_points = []

        self.concepts = munch.Munch({})
        self.concept_render_points = []


        self.conceptions = munch.Munch({})
        self.conception_render_points = []

        self._calculate_components(
            state_ao.get_state('dynamic').get('hero').get('capital')
        )


    def _calculate_components(
        self,
        player_capital: munch.Munch
    ) -> None:
        """_summary_

        :param player_capital: _description_
        :type player_capital: munch.Munch

        .. note::
            The label of a bauble must map to the possible label in a _Sprite_'s `capital`, i.e. `equipment[].label`, `armory[].label`, `inventory.label`, etc.
        .. note::
            In other words, the possible values of `component.label` are `armor | shield | thrust | shoot | slash | cast | bag | belt`. TODO: there will probably be more to add here.
        """
        if not self.components:
            return

        display_num = 0

        log.debug(f'Initializing {self.name} thought...', 'Thought._init_components')
        
        for i, component in enumerate(self.components):

            
            if not component:
                continue

            log.debug(f'Initializing {component.label} {component.component}', 'Thought._init_components')
            if component.component == 'bauble':
                if component.label in ['slash', 'thrust', 'shoot', 'cast']:
                    iter_set = player_capital.get('armory')
                elif component.label in ['armor', 'shield']:
                    iter_set = player_capital.get('equipment')
                elif component.label in ['bag', 'belt']:
                    iter_set = player_capital.get('inventory')

                component_avatars = [
                    arm.component 
                    for arm in iter_set
                    if arm.label == component.label
                ]

                setattr(
                    self.baubles, 
                    component.label, 
                    munch.Munch({
                        'enabled': component_avatars,
                        'selected': None,
                    })
                )

                # How to set this up so the bauble row length
                # is fit to the number of items in the player's
                # state?

            elif component.component == 'display':
                display_num += 1
                setattr(
                    self.displays,
                    component.label,
                    None
                )
                # TODO: set display based on player state
        
        if len(self.baubles) > 0:
            self._calculate_bauble_positions()
            self._calculate_bauble_avatar_positions()

        # TODO: what to do if both baubles and diplay?


    # TODO: candidate for cython formulae module
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

        log.debug(f'Initializing {self.name} bauble positions', '_init_bauble_positions')
        bauble_piece_widths = [ 
            piece.size.w 
            for piece 
            in self.components_conf.bauble.enabled.values() 
        ]
        bauble_width = sum(bauble_piece_widths)
        # NOTE: here is where the height assumption is made. See note in docstring.
        bauble_height = self.components_conf.bauble.enabled.left.size.h
        bauble_padding = (
            self.device_dim[0] * self.styles.padding.w,
            self.device_dim[1] * self.styles.padding.h
        )
        bauble_margins = (
            self.styles.margins.w * bauble_width,
            self.styles.margins.h * bauble_height
        )

        if self.styles.stack == 'vertical':
            canvas_dim = (
                self.alignment_ref[0],
                self.device_dim[1]
            )
            canvas_start = (
                bauble_padding[0],
                self.alignment_ref[1]
            )
            self.bauble_scroll_num = canvas_dim[1] // bauble_height

        elif self.styles.stack == 'horizontal':
            canvas_dim=(
                self.device_dim[0],
                self.device_dim[1] - self.alignment_ref[1] - \
                    self.alignment_dim[1]
            )
            canvas_start = (
                bauble_padding[0],
                self.alignment_ref[1] + self.alignment_dim[1] + \
                    bauble_padding[1]
            )
            self.bauble_scroll_num = canvas_dim[0] // bauble_width

        # NOTE: this is a hardcoded layout for bauble-only tab

        # what if tab has both baubles and displays? 
        # what if tab has more baubles than can be displayed?
        # how to map player equipment and inventory to bauble?


        # NOTE:number of bauble rows
        #       -> shifts the y coordinate by row height
        for i in range(len(self.baubles)):
            # NOTE: number of baubles displayed
            #       -> determines starting position of pieces
            for j in range(self.bauble_scroll_num):

                if j ==  0:
                    self.bauble_render_points.append(
                        (
                            canvas_start[0],
                            canvas_start[1]+ i*(bauble_height + bauble_margins[1])
                        )
                    )
                    self.bauble_piece_map.append('left')
                    continue

                # NOTE: recall the sum(width(piece)) = width(bauble)
                #       i.e. only need to accumulate piece width

                if j == 1: # add left piece
                    piece_width = bauble_piece_widths[0]
                else: # add middle piece
                    piece_width = bauble_piece_widths[1]
                # don't add right piece width because nothing 
                # is rendered after that

                if j != self.bauble_scroll_num - 1:
                    self.bauble_piece_map.append('middle')
                else:
                    self.bauble_piece_map.append('right')


                last_index = len(self.bauble_render_points) - 1
                self.bauble_render_points.append(
                    (
                        self.bauble_render_points[last_index][0] + piece_width,
                        self.bauble_render_points[last_index][1]
                    )
                )


    def _calculate_bauble_avatar_positions(
        self
    ) -> None:
        log.debug(f'Calcuating {self.name} bauble avatar positions', '_calculate_bauble_avatar_positions')
        bauble_piece_widths = [ 
            piece.size.w 
            for piece 
            in self.components_conf.bauble.enabled.values() 
        ]
        bauble_width = sum(bauble_piece_widths)
            # NOTE: here is where the height assumption is made. See note in docstring.
        bauble_height = self.components_conf.bauble.enabled.left.size.h

        for bauble_label, bauble_conf in self.baubles.items():
            row = filter(
                lambda x: x.label == bauble_label, 
                self.components
            )
            row_index = self.components.index(row)
            start_index = row_index * len(self.baubles)
            start_point = self.bauble_render_points[start_index]
            added = 0

            for avatar_key in bauble_conf.enabled:
                if bauble_label in ['slash', 'shoot', 'cast', 'thrust']:
                    avatar_dim = (
                        self.avatar_conf.armory.get(avatar_key).size.w,
                        self.avatar_conf.armory.get(avatar_key).size.h
                    )
                elif bauble_label in ['armor', 'shield']:
                    avatar_dim = (
                        self.avatar_conf.equipment.get(avatar_key).size.w,
                        self.avatar_conf.equipment.get(avatar_key).size.w,
                    )
                elif bauble_label in ['bag', 'belt']:
                    avatar_dim = (
                        self.avatar_conf.inventory.get(avatar_key).size.w,
                        self.avatar_conf.inventory.get(avatar_key).size.h
                    )

                self.bauble_avatar_render_points.append(
                    (
                        start_point[0] + (bauble_width - avatar_dim[0])/2,
                        start_point[1] + (bauble_height - avatar_dim[1])/2
                    )
                )

                added += 1

                if added == self.bauble_scroll_num:
                    break
            
            if self.bauble_scroll_num > added:
                while self.bauble_scroll_num > added:
                    self.bauble_avatar_render_points.append(None)
                    added + 1
     

    def _calculate_bauble_avatar_map(self):
        for bauble_conf in self.baubles.values():
            added = 0
            total_baubles = len(bauble_conf.enabled)

            for avatar_key in bauble_conf.enabled:
                self.bauble_avatar_map.append(avatar_key)
                added += 1
                
                if added == self.bauble_scroll_num:
                    break

            if self.bauble_scroll_num > added:
                while self.bauble_scroll_num > total_baubles:
                    self.bauble_avatar_map.append(None)

            # TODO: will need the current world state to update grab player's capital

        self.baubles.keys() # bauble labels
        # need to  

    def _calculate_bauble_frame_map(self):
        for bauble_label, bauble_conf in self.baubles.items():
            pass
            # TODO: need to ensure teh selected bauble for a bauble_label has its frame
            # set to active

    def has_baubles(self):
        return len(self.baubles) > 0


    def bauble_maps(self):
        return self.bauble_frame_map, self.bauble_piece_map, self.bauble_avatar_map


    def rendering_points(
        self,
        component_key: str
    ) -> Union[list, None]:
        if component_key == 'bauble':
            return self.bauble_render_points
        return None


    def update(
        self
    ):
        # TODO:
        # if some condition to prevent too many updates
        self._calculate_bauble_frame_map()
        self._calculate_bauble_avatar_map()