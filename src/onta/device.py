import onta.settings as settings
import onta.load.conf as conf

class Device():

    desired_screen_width = None
    desired_screen_height = None
    dimensions = None
    
    def __init__(self, 
        screen_width: int = settings.SCREEN_DEFAULT_WIDTH, 
        screen_height: int = settings.SCREEN_DEFAULT_HEIGHT
    ) -> None:
        self.desired_screen_width = screen_width
        self.desired_screen_height = screen_height
        self._determine_dimensions()

    def _determine_dimensions(self):
        # TODO: pull device information and see if desired is possible
        self.dimensions = (self.desired_screen_width, self.desired_screen_height)