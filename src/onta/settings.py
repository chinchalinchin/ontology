import os


APP_DIR = os.path.dirname(os.path.abspath(__file__))
"""Folder containing the root module of the project"""

PROJECT_DIR = os.path.dirname(APP_DIR)
"""Folder containing the project source"""


ASSET_DIR = os.path.join(APP_DIR, 'data', 'assets')
"""Directory containing application assets."""

CONF_DIR = os.path.join(ASSET_DIR, 'conf')
"""Directory containing application configuration"""

SPRITE_DIR = os.path.join(ASSET_DIR, 'sprites')
"""Diretory containing spritesheets"""