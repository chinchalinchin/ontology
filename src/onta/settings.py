import os


APP_DIR = os.path.dirname(os.path.abspath(__file__))
"""Directory containing the root module of the project"""

SRC_DIR = os.path.dirname(APP_DIR)
"""Directory containing the project source"""

ASSET_DIR = os.path.join(SRC_DIR, 'data', 'assets')
"""Directory containing application assets."""

CONF_DIR = os.path.join(ASSET_DIR, 'conf')
"""Directory containing application configuration"""

SPRITE_DIR = os.path.join(ASSET_DIR, 'sprites')
"""Diretory containing spritesheets"""

SHEET_SIZE = (832, 1344)