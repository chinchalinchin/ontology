class Player(Asset):
    # Inherited Attributes
    ## Asset Identifier
    asset_key: str
    ## Properties
    dimensions: Tuple[int, int]
    ## State
    frame_key: str
    layer_key: str
    position: Tuple[int, int]

    # Unique Attributes
    ## Properties
    hitboxes: List[Tuple[int, int, int, int]]
    mappings: dict
    ## Extensions
    device: Controller | Keyboard

    def __init__(self, 
        device_type = Enum["controller" | "keyboard"]
    ):
        if device_type == "controller":
            self.device = Controller()
        else:
            self.device = Keyboard(mapping)

    def update(self, intention: Intent) -> None:
        # Abstract implementation
        # Update state

    def poll(self) -> Intent:
        intention = self.device.intend()
        # Map device to intent
        return Intent(intention)