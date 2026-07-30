# NOTE: PSEUDCODE
#       Should be implemented in Cython, I think.

class Screen:
    # Static image assembled from immutable assets
    canvas: Image
    # Buffer to hold copy of canvas for rendering
    buffer: Image
    # Screen size
    screen: Tuple[int, int]


    def __init__(self, 
        screen: Tuple[int, int], 
        immutable: List[Asset]
    ):
        self.screen = screen
        self.canvas(immutable)
        return

    def _onscreen(self, 
        pov: Tuple[int, int], 
        pos: Tuple[int, int], 
        dim: Tuple[int, int]
    ) -> bool:
        result = False
        # calculate result
        return result
    
    def canvas(self, 
        assets: List[Asset]
    ) -> Image:
        """
        Render and stack immutable assets onto static canvas.
        """
        for asset in assets:
            position, dimensions, frame = asset.get()
            self.canvas.render(position, dimensions, frame)

        return self.canvas

    def draw(self, 
        assets : List[Asset], 
        pov: Tuple[int, int]
    ) -> Image:
        """
        Render mutable assets onto the immutable canvas.
        """
        # 1. Copy static canvas into new buffer
        self.buffer = self.canvas.copy()

        # 2. Render all onscreen assets
        for asset in assets:
            position, dimensions, frame = asset.get()
            if self._onscreen(pov, position, dimensions):
                self.buffer.render(position, dimensions, frame)
        
        # 3. Clip bufer to the player's POV
        self.buffer.clip(pov)
        return self.buffer