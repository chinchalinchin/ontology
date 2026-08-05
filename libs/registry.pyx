# cython: language_level=3
"""
# Ontology: Asset Registry

Cythonized extension for ingesting physical image files, tracking their GPU memory pointers 
and flat-mapping FrameKeys directly to GPU texture croppings. 
"""

import os
from typing import Tuple

from libs.render cimport _renderer, SDL_Texture, SDL_DestroyTexture, SDL_QueryTexture
import libs.render as render
import app.constants as constants
from app.models.configuration import (
    PySheetPropertyConfiguration,
    PyObjectPropertyConfiguration,
    PyEffectPropertyConfiguration,
    PyCursorPropertyConfiguration,
    PyTilePropertyConfiguration
)

cdef extern from "SDL2/SDL_image.h":
    SDL_Texture* IMG_LoadTexture(SDL_Renderer* renderer, const char* file)

cdef class TexturePtr:
    """
    Cython extension type wrapping the raw C-pointer for an SDL_Texture.
    Provides automated memory leak prevention on pointer garbage collection.
    """
    def __dealloc__(self):
        if self.ptr != NULL:
            SDL_DestroyTexture(self.ptr)
            self.ptr = NULL

class Registry:
    """
    Centralized Asset Registry to ingest configuration, cache GPU textures, 
    and map dynamic string keys to crop coordinates.
    """
    def __init__(self):
        self._textures = {}
        self._frames = {}

        self._load()
        self._cache()
        self._assemble()
        self._index()

    def _load(self):
        """Invoke Pydantic schema engines to strictly parse configuration YAML files."""
        self.sheets_config = PySheetPropertyConfiguration()
        self.objects_config = PyObjectPropertyConfiguration()
        self.effects_config = PyEffectPropertyConfiguration()
        self.cursors_config = PyCursorPropertyConfiguration()
        self.tiles_config = PyTilePropertyConfiguration()

    def load(self, filepath: str) -> TexturePtr:
        """Loads a physical .png file directly into GPU memory via SDL2 extensions."""
        cdef bytes b_filepath = filepath.encode('utf-8')
        cdef SDL_Texture* tex = IMG_LoadTexture(_renderer, b_filepath)
        
        if tex == NULL:
            raise RuntimeError(f"Failed to load texture into GPU memory: {filepath}")

        cdef int w, h
        SDL_QueryTexture(tex, NULL, NULL, &w, &h)

        cdef TexturePtr wrapper = TexturePtr()
        wrapper.ptr = tex
        wrapper.w = w
        wrapper.h = h
        return wrapper

    def _cache(self):
        """Recursively parses all physical PNG files across the static asset directory."""
        asset_dir = str(constants.ASSET_DIR)
        for root, _, files in os.walk(asset_dir):
            for file in files:
                if file.endswith('.png'):
                    asset_key = file[:-4]
                    filepath = os.path.join(root, file)
                    self._textures[asset_key] = self.load(filepath)

    def _assemble(self):
        """Compiles composite characters utilizing cython-wrapped base and feature renders."""
        if not self.sheets_config or not self.sheets_config.sprites:
            return

        for persona in getattr(self.sheets_config.sprites, 'compositions', []):
            base_ptr = self._textures.get(persona.base)
            if not base_ptr:
                continue

            feature_ptrs = []
            feats = persona.features if hasattr(persona, 'features') else []
            apparel = persona.apparel if hasattr(persona, 'apparel') else []
            
            for f_key in list(feats) + list(apparel):
                if f_key in self._textures:
                    feature_ptrs.append(self._textures[f_key])

            if feature_ptrs:
                self._textures[persona.key] = render.compose(base_ptr, feature_ptrs)

    def _index(self):
        """Maps runtime dynamic frame keys to their GPU mapping tuple coordinates."""
        
        # 1. Binary Objects (Chests, Gates, Plates)
        if self.objects_config:
            for cat in ['chests', 'gates', 'plates']:
                for key, obj in getattr(self.objects_config, cat, {}).items():
                    if key in self._textures:
                        w, h = obj.shape.dim.l, obj.shape.dim.w
                        self._frames[f"{key}-idle"] = (self._textures[key], 0, 0, w, h)
                        self._frames[f"{key}-activated"] = (self._textures[key], w, 0, w, h)

        # 2. Sprites
        if self.sheets_config and self.sheets_config.sprites:
            w = self.sheets_config.sprites.shape.dim.l
            h = self.sheets_config.sprites.shape.dim.w

            # Apply mapping across all Sprite assets against the LPC schema configuration
            for s_key in self._textures:
                for action, action_prop in self.sheets_config.sprites.actions.items():
                    for direction, dir_prop in action_prop.directions.items():
                        row = dir_prop.row
                        count = action_prop.count
                        for f in range(count):
                            self._frames[f"{s_key}-{action}-{direction}-{f}"] = (
                                self._textures[s_key], f * w, row * h, w, h
                            )

        # 3. Pixies
        if self.sheets_config and getattr(self.sheets_config, 'pixies', None):
            for key, pixie_prop in getattr(self.sheets_config.pixies, 'shapes', {}).items():
                if key in self._textures:
                    w, h = pixie_prop.dim.l, pixie_prop.dim.w
                    for action, action_prop in getattr(self.sheets_config.pixies, 'action', {}).items():
                        count = getattr(action_prop, 'count', 4)  # Default fallback handling
                        for row, direction in enumerate(action_prop.directions):
                            for f in range(count):
                                self._frames[f"{key}-{direction}-{f}"] = (
                                    self._textures[key], f * w, row * h, w, h
                                )

        # 4. Effects
        if self.effects_config:
            for cat in ['persistent', 'temporary']:
                for key, eff in getattr(self.effects_config, cat, {}).items():
                    if key in self._textures:
                        w, h = eff.shape.dim.l, eff.shape.dim.w
                        for f in range(eff.count):
                            self._frames[f"{key}-{f}"] = (
                                self._textures[key], f * w, 0, w, h
                            )

    def data(self, frame_key: str) -> Tuple:
        """
        Returns a lightweight Python tuple resolving mapped texture configurations for the camera.
        Format: (TexturePtr, src_x, src_y, src_w, src_h)
        """
        if frame_key in self._frames:
            return self._frames[frame_key]
            
        # Fallback for single-frame immutables like Tiles where schema crop === texture bounds
        elif frame_key in self._textures:
            tex = self._textures[frame_key]
            return (tex, 0, 0, tex.w, tex.h)
            
        return None