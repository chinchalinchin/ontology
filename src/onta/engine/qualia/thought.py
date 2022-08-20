
from typing import Union
import munch

import onta.settings as settings
import onta.loader.state as state
import onta.util.logger as logger 

log = logger.Logger('onta.engine.qualia.thought', settings.LOG_LEVEL)

class Thought():

    def __init__(
        self, 
        name: str,
        components: list, 
        components_conf: munch.Munch,
        styles: munch.Munch, 
        alignment_reference: tuple,
        alignment_dim: tuple,
        device_dim: tuple,
        state_ao: state.State
    ) -> None:        
        self.name = name
        self.components = components
        self.components_conf = components_conf
        self.styles = styles
        self.alignment_ref = alignment_reference
        self.alignment_dim = alignment_dim
        self.device_dim = device_dim

        # Define in __init__ to avoid closure since tabs are created in loop by Menu
        self.baubles = munch.Munch({})
        self.bauble_render_points = []
        self.bauble_frame_map = []
        self.bauble_piece_map = []
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

        self._init_components(state_ao)

    def _init_player_mapping(
        self,
        state_ao: state.State
    ) -> None:
        for comp in self.components:
            comp.label, comp.component
            hero_capital = state_ao.get_state('dynamic').get('hero').get('capital')

            if comp.component == 'bauble':
                if comp.label in ['slash', 'thrust', 'shoot', 'cast']:
                    component_armory_avatars = [
                        arm.component 
                        for arm in hero_capital.get('armory')
                        if arm.label == comp.label
                    ]

                    pass

    def _init_components(
        self,
        state_ao: state.State
    ) -> None:
        """_summary_

        :param state_ao: _description_
        :type state_ao: state.State

        .. note::
            The label of a bauble must map to the possible label in a _Sprite_'s `capital`, i.e. `equipment[].label`, `armory[].label`, `inventory.label`, etc.
        .. note::
            In other words, the possible values of `component.label` are `armor | shield | thrust | shoot | slash | cast | bag | belt`. TODO: there will probably be more to add here.
        """
        if not self.components:
            return

        display_num = 0

        log.debug(f'Initializing {self.name} thought...', 'Thought._init_components')
        
        hero_capital = state_ao.get_state('dynamic').get('hero').get('capital')

        for i, component in enumerate(self.components):

            
            if not component:
                continue

            log.debug(f'Initializing {component.label} {component.component}', 'Thought._init_components')
            if component.component == 'bauble':
                if component.label in ['slash', 'thrust', 'shoot', 'cast']:
                    iter_set = hero_capital.get('armory')
                elif component.label in ['armor', 'shield']:
                    iter_set = hero_capital.get('equipment')
                elif component.label in ['bag', 'belt']:
                    iter_set = hero_capital.get('inventory')

                component_avatars = [
                    arm.component 
                    for arm in iter_set
                    if arm.label == component.label
                ]

                setattr(
                        self.baubles,
                        component.label,
                        component_avatars
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
            self._init_bauble_positions()
            self._init_bauble_avatar_positions()

        # TODO: what to do if both baubles and diplay?

    # TODO: candidate for cython formulae module
    def _init_bauble_positions(
        self,
    ) -> None:
        """_summary_

        .. note::
            Method is dependent on all baubles being the same height. Widths are free to vary. In other words, the baubles are constructed from horizontal pieces only. They cannot be broken up vertically.
        .. note::
            Starting points are dependent on stack style, but the baubles are always organized into rows.
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

        print('bauble width', bauble_width)
        print('bauble height', bauble_height)
        print('canvas dim', canvas_dim)
        print('canvas start', canvas_start)

        print('len(self.baubles)', len(self.baubles))
        print('self.bauble_scroll_num', self.bauble_scroll_num)

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
                    self.bauble_frame_map.append('enabled')
                    print(self.bauble_render_points)
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

                self.bauble_frame_map.append('enabled')

                last_index = len(self.bauble_render_points) - 1
                self.bauble_render_points.append(
                    (
                        self.bauble_render_points[last_index][0] + piece_width,
                        self.bauble_render_points[last_index][1]
                    )
                )
                print(self.bauble_render_points)


    def _init_bauble_avatar_positions(
        self
    ) -> None:
        pass


    def _calculate_bauble_avatar_map(self):
        self.baubles.keys() # bauble labels
        # need to 


    def has_baubles(self):
        return len(self.baubles) > 0


    def bauble_maps(self):
        return self.bauble_frame_map, self.bauble_piece_map


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
        pass
        # TODO