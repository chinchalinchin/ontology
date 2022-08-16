
from typing import Union
import munch

import onta.settings as settings
import onta.loader.state as state
import onta.util.logger as logger 

log = logger.Logger('onta.engine.qualia.tab', settings.LOG_LEVEL)

class Tab():

    baubles = munch.Munch({})
    displays = munch.Munch({})
    indicators = munch.Munch({})
    labels = munch.Munch({})

    bauble_render_points = []
    display_render_points = []
    indicator_render_points = []
    label_render_points = []

    heading_points = []

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
        self._init_components(state_ao)


    def _init_components(
        self,
        state_ao: state.State
    ) -> None:
        if not self.components:
            return

        bauble_num = 0
        display_num = 0

        for i, component in enumerate(self.components):
            if not component:
                continue

            self.alignment_ref
            if component.component == 'bauble':
                bauble_num += 0


                # calculate bauble points
                setattr(
                    self.baubles,
                    component.label,
                    None
                )
                # TODO: set baubles based on player state

            elif component.component == 'display':
                display_num += 1
                # calculate display points
                setattr(
                    self.display,
                    component.label,
                    None
                )
                # TODO: set display based on player state
        
        if bauble_num > 0:
            self._init_bauble_positions(bauble_num)


    def _init_bauble_positions(
        self,
        bauble_num
    ) -> None:
        bauble_piece_widths = [ piece.size.w for piece in self.components_conf.bauble.enabled.values() ]
        bauble_width = sum(bauble_piece_widths)
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
                self.device_dim[0] - self.alignment_ref[0],
                self.device_dim[1]
            )
            canvas_start = (
                bauble_padding[0],
                self.alignment_ref[1]
            )
            bauble_scroll_num = canvas_dim[1] // bauble_height

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
            bauble_scroll_num = canvas_dim[0] // bauble_width

        # starting point is dependent on stack style, but baubles are always rows 

        # number of bauble rows
            # shifts the y coordinate by row height
        for i in range(bauble_num):
            # number of baubles displayed
                # determines starting position of pieces
            for j in range(bauble_scroll_num):

                if i == j ==  0:
                    self.bauble_render_points.append(
                        canvas_start
                    )
                    continue

                # NOTE: recall the sum(width(piece)) = width(bauble)
                #           i.e. only need to accumulate piece width

                if j == 0: # left piece
                    piece_width = bauble_piece_widths[0]
                elif j == bauble_scroll_num - 1: # right piece
                    piece_width = bauble_piece_widths[2]
                else: # middle piece
                    piece_width = bauble_piece_widths[1]

                self.bauble_render_points.append(
                    self.bauble_render_points[i+j-1][0] + piece_width,
                    self.bauble_render_points[i+j-1][1] + i*(bauble_height + bauble_margins[1])
                )

    def get_render_points(
        self,
        component_key: str
    ) -> Union[list, None]:
        if component_key == 'bauble':
            return self.bauble_render_points
        return None