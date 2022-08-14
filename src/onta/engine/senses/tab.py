
import munch


import onta.device as device


class Tab():


    def __init__(
        self, 
        components: munch.Munch, 
        stack_style: str, 
        alignment_reference: tuple,
        player_device: device.Device
    ) -> None:
        self.components = components
        self.stack_style = stack_style
        self.alignment_ref = alignment_reference
        self.player_device = player_device
        self._init_components()

    def _init_components(
        self
    ) -> None:
        if not self.components:
            return
            
        for component in self.components:
            if not component:
                continue

            if component.component == 'bauble':
                component.label

            elif component.component == 'map':
                component.label