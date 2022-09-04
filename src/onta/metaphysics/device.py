from onta.metaphysics \
    import settings

class Device():

    def __init__(self, 
        screen_width: int = settings.SCREEN_DEFAULT_WIDTH, 
        screen_height: int = settings.SCREEN_DEFAULT_HEIGHT
    ) -> None:
        self.desired_screen_width = screen_width
        self.desired_screen_height = screen_height
        self._determine_dimensions()

    def _determine_dimensions(self):
        # TODO: pull device information and see if desired is possible
        self.dimensions = (
            self.desired_screen_width, 
            self.desired_screen_height
        )