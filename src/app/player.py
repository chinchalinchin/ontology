# NOTE: pseudo code

class Player:
    device: Controller | Keyboard

    def __init__(self, 
        device_type = Enum["controller" | "keyboard"]
    ):
        if device_type == "controller":
            self.device = Controller()
        else:
            self.device = Keyboard(mapping)

    def poll(self) -> SpriteState:
        # Map device to state
        return SpriteState(
            # TODO: init
        )