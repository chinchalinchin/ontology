import os


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

TILE_DIR = os.path.join(IMG_DIR, 'tiles')

STRUT_DIR = os.path.join(IMG_DIR, 'struts')

DEFAULT_WIDTH = int(os.environ.setdefault('DEFAULT_WIDTH', '800'))
"""Default GUI width"""

DEFAULT_HEIGHT = int(os.environ.setdefault('DEFAULT_HEIGHT', '600'))
"""Default GUI height"""

LOG_LEVEL = "DEBUG"
"""Log level for capturing stdout"""