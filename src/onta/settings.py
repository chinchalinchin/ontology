import os

# Directory Configuration

APP_DIR = os.path.dirname(os.path.abspath(__file__))
"""Directory containing the root module of the project"""

SRC_DIR = os.path.dirname(APP_DIR)
"""Directory containing the project source"""

ASSET_DIR = os.path.join(SRC_DIR, 'data', 'assets')
"""Directory containing application assets."""

CONF_DIR = os.path.join(ASSET_DIR, 'conf')
"""Directory containing application configuration"""

STATE_DIR = os.path.join(ASSET_DIR, 'state')
"""Directory containg state information"""

IMG_DIR = os.path.join(ASSET_DIR, 'img')
"""Diretory containing image assets"""

SPRITE_DIR = os.path.join(IMG_DIR, 'sprites')
"""Directory containing spritesheets"""

TILE_DIR = os.path.join(IMG_DIR, 'tiles')
"""Directory containing tile sheets"""

STRUT_DIR = os.path.join(IMG_DIR, 'struts')
"""Directory containing strut sheets"""

# Debug Configuration

LOG_LEVEL = "DEBUG"
"""Log level for capturing stdout"""

# GUI Configuration

DEFAULT_WIDTH = int(os.environ.setdefault('DEFAULT_WIDTH', '800'))
"""Default GUI width"""

DEFAULT_HEIGHT = int(os.environ.setdefault('DEFAULT_HEIGHT', '600'))
"""Default GUI height"""

# Asset Configuration

SPRITESHEET_DIM = (832, 1344)
"""Dimensions of spritesheets"""

TILE_DIM = (96, 32)
"""Dimensions of a tile"""

IMG_MODE = "RGB"
"""
Rendering mode for application images

see [PIL docs](https://pillow.readthedocs.io/en/stable/handbook/concepts.html#modes) for more information.
"""

IMG_BLANK = (255, 255, 255)
"""
Color channels for a blank screen for the given rendering mode. If `IMG_MODE == 'RGB'`, then this should be set to a 3-tuple such as (255,255,255). If `IMG_MODE == 'RGBA'`, then this should be set to (255, 255, 255, 1). And so on for a given image mode.

see [PIL docs](https://pillow.readthedocs.io/en/stable/handbook/concepts.html#modes) for more information.
"""

# Game Loop Configuration

FPS=25
"""Framerate for the rendering engine"""