import os

# Directory Configuration

# TODO: will need to wrap this in an object and allow user to base in data_dir if I want ontologies to be completely passed in through command line

APP_DIR = os.path.dirname(os.path.abspath(__file__))
"""Directory containing the root module of the project"""

SRC_DIR = os.path.dirname(APP_DIR)
"""Directory containing the project source"""

DEFAULT_DIR = os.path.join(SRC_DIR, 'data')
"""Directory containg application data"""

CONF_PATH = [ 
    'conf' 
]
"""Array containing path parts relative to ontology directory leading to application configuration directory"""

STATE_PATH = [ 
    'state' 
]
"""Array containing path parts relative to ontology directory leading to state information directory"""

SPRITE_PATH = [ 
    'assets', 
    'entities', 
    'sprites' 
]
"""Array containing path parts relative to ontology directory leading to spritesheets directory"""

TILE_PATH = [ 
    'assets', 
    'forms', 
    'tiles' 
]
"""Array containing path parts relative to ontology directory leading to tilesheet directory"""

STRUT_PATH = [ 
    'assets', 
    'forms', 
    'struts' 
]
"""Array containing path parts relative to ontology directory leading to strutsheet directory"""

PLATE_PATH = [ 
    'assets', 
    'forms', 
    'plates' 
]
"""Array containing path parts relative to ontology directory leading to platesheet directory"""

AVATAR_PATH = [ 
    'assets', 
    'self', 
    'avatars' 
]

DISPLAY_PATH = [ 
    'assets', 
    'self', 
    'display' 
]

MIRROR_PATH = [ 
    'assets', 
    'self', 
    'mirrors' 
]

SLOT_PATH = [ 
    'assets', 
    'self', 
    'slots' 
]

# Debug Configuration

LOG_LEVEL = os.environ.setdefault('LOG_LEVEL', 'DEBUG')
"""Log level for capturing stdout"""

# GUI Configuration

SCREEN_WIDTH = int(os.environ.setdefault('SCREEN_WIDTH', '800'))
"""Default GUI width"""

SCREEN_HEIGHT = int(os.environ.setdefault('SCREEN_HEIGHT', '600'))
"""Default GUI height"""

# Rendering Configuration

IMG_MODE = "RGBA"
"""
Rendering mode for application images

see [PIL docs](https://pillow.readthedocs.io/en/stable/handbook/concepts.html#modes) for more information.
"""

IMG_BLANK = (255, 255, 255, 0)
"""
Color channels for a blank screen for the given rendering mode. If `IMG_MODE == 'RGB'`, then this should be set to a 3-tuple such as (255,255,255). If `IMG_MODE == 'RGBA'`, then this should be set to (255, 255, 255, 1). And so on for a given image mode.

see [PIL docs](https://pillow.readthedocs.io/en/stable/handbook/concepts.html#modes) for more information.
"""

FPS=30
"""Framerate for the rendering engine"""

