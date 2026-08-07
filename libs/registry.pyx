# cython: language_level=3
"""
# Ontology: Asset Registry

Cythonized extension for ingesting physical image files, tracking their GPU memory pointers and flat-mapping Frame keys directly to GPU texture croppings. 
"""
# Standard Libraries
import os
from typing import Tuple

# Application Libraries
import app.config.constants as constants
from app.config.validators import (
    PySheetPropertyConfiguration,
    PyObjectPropertyConfiguration,
    PyEffectPropertyConfiguration,
    PyCursorPropertyConfiguration,
    PyTilePropertyConfiguration,
    PyCraftPropertyConfiguration,
    PyRecipeConfiguration
)
from app.config.hierarchy import FrameRecipe, AnimationRecipe

# Cython Libraries
from libs.render cimport (
    _renderer, 
    SDL_Renderer, 
    SDL_Texture, 
    SDL_DestroyTexture, 
    SDL_QueryTexture
)
import libs.render as render

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

        self._configuration()
        self._cache()
        self._assemble()
        self._index()

    def _configuration(self):
        """Invoke Pydantic schema engines to strictly parse configuration YAML files."""
        self.recipes_config = PyRecipeConfiguration()
        self.sheets_config = PySheetPropertyConfiguration()
        self.objects_config = PyObjectPropertyConfiguration()
        self.effects_config = PyEffectPropertyConfiguration()
        self.cursors_config = PyCursorPropertyConfiguration()
        self.tiles_config = PyTilePropertyConfiguration()
        self.crafts_config = PyCraftPropertyConfiguration()

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
        if not getattr(self, 'sheets_config', None) or not getattr(self.sheets_config, 'sheets', None):
            return

        for cat in ['pixies', 'sprites']:
            sheet_cfg = getattr(self.sheets_config.sheets, cat, None)
            if not sheet_cfg: continue

            for p_key, persona in sheet_cfg.personas.items():
                if not persona.stack: continue
                base_key = persona.stack[0]
                base_ptr = self._textures.get(base_key)
                if not base_ptr: continue
                
                feature_ptrs = []
                for f_key in persona.stack[1:]:
                    if f_key in self._textures:
                        feature_ptrs.append(self._textures[f_key])

                if feature_ptrs:
                    self._textures[p_key] = render.compose(base_ptr, feature_ptrs)
                else:
                    self._textures[p_key] = base_ptr

    def _index(self):
        """Maps runtime dynamic frame keys to their GPU mapping tuple coordinates."""
        prop_map = {
            "tiles": self.tiles_config.tiles 
                        if getattr(self, 'tiles_config', None) else None,
            "objects": self.objects_config.objects 
                        if getattr(self, 'objects_config', None) else None,
            "effects": self.effects_config.effects 
                        if getattr(self, 'effects_config', None) else None,
            "cursors": self.cursors_config.cursors 
                        if getattr(self, 'cursors_config', None) else None,
            "crafts": self.crafts_config.objects 
                        if getattr(self, 'crafts_config', None) else None,
            "sheets": self.sheets_config.sheets 
                        if getattr(self, 'sheets_config', None) else None,
        }

        for cat_name, cat_props in prop_map.items():
            if not cat_props: continue
            
            cat_recipes = getattr(self.recipes_config.assets, cat_name, None)
            if not cat_recipes: continue
            
            # Iterate through the Pydantic PyRecipe model fields
            for inst_name, recipe in cat_recipes:
                if not recipe: continue
                
                inst_props = getattr(cat_props, inst_name, None)
                if not inst_props: continue

                # 1. SingleFrame 
                if recipe.frame == FrameRecipe.SINGLE:
                    # Tiles schema has a list of keys; others map key -> properties
                    if cat_name == "tiles":
                        w, h = inst_props.dim.l, inst_props.dim.w
                        for key in inst_props.keys:
                            if key in self._textures:
                                self._frames[key] = (self._textures[key], 0, 0, w, h)
                    else:
                        for key, props in inst_props.items():
                            if key in self._textures:
                                w, h = props.dim.l, props.dim.w
                                self._frames[key] = (self._textures[key], 0, 0, w, h)

                # 2. IterableFrame
                elif recipe.frame == FrameRecipe.ITERABLE:
                    for key, props in inst_props.items():
                        if key not in self._textures: continue
                        w, h = props.dim.l, props.dim.w
                        
                        # Differentiate between Binary Objects and Sequential Effects
                        if recipe.animation == AnimationRecipe.BINARY:
                            self._frames[f"{key}-idle"] = (self._textures[key], 0, 0, w, h)
                            self._frames[f"{key}-activated"] = (self._textures[key], w, 0, w, h)
                        else:
                            for f in range(props.count):
                                self._frames[f"{key}-{f}"] = (self._textures[key], f * w, 0, w, h)

                # 3. StateFrame (Sheets)
                elif recipe.frame == FrameRecipe.STATE:
                    for p_key, persona in inst_props.personas.items():
                        if p_key not in self._textures: continue
                        w, h = persona.dim.l, persona.dim.w
                        
                        for action, action_prop in inst_props.actions.items():
                            for direction, dir_prop in action_prop.directions.items():
                                row = dir_prop.row
                                for f in range(action_prop.count):
                                    self._frames[f"{p_key}-{action}-{direction}-{f}"] = (
                                        self._textures[p_key], f * w, row * h, w, h
                                    )

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