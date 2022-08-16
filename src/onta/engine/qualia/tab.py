
import munch


class Tab():

    baubles = None
    displays = None

    def __init__(
        self, 
        name: str,
        components: list, 
        components_conf: munch.Munch,
        stack_style: str, 
        alignment_reference: tuple,
        alignment_dim: tuple,
        device_dim: tuple
    ) -> None:
        self.name = name
        self.components = components
        self.components_conf = components_conf
        self.stack_style = stack_style
        self.alignment_ref = alignment_reference
        self.alignment_dim = alignment_dim
        self.device_dim = device_dim
        self._init_components()


    def _init_components(
        self
    ) -> None:
        if not self.components:
            return
            
        for i, component in enumerate(self.components):
            if not component:
                continue

            self.alignment_ref
            self.player_device

            if self.stack_style == 'vertical':
                if component.component == 'bauble':
                    component.label

                elif component.component == 'map':
                    component.label

            elif self.stack_style == 'horizontal':
                if component.component == 'bauble':
                    component.label

                elif component.component == 'map':
                    component.label