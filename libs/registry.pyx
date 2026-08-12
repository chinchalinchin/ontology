# cython: language_level=3
"""
# Ontology: Asset Registry

Cythonized extension for ingesting physical image files, tracking their GPU memory pointers and flat-mapping Frame keys directly to GPU texture croppings. 
"""
# Standard Libraries
import os
import logging
from typing import Tuple

# Application Libraries
from app.config.enums import (
    FrameRecipe, 
    AnimationRecipe, 
    AssetCategories,
    AssetInstances
)
import app.config.settings as settings

# Cython Libraries
from libs.render cimport (
    _renderer, 
    SDL_Renderer, 
    SDL_Texture, 
    SDL_DestroyTexture, 
    SDL_QueryTexture
)
import libs.render as render

logger = logging.getLogger("libs.registry")

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
    
    def __init__(self, properties, recipes):
        logger.debug("Initializing Asset Registry...")
        self._textures = {}
        self._frames = {}
        self.properties = properties
        self.recipes = recipes

        self._cache()
        self._assemble()
        self._index()

    def _cache(self):
        """Recursively parses all physical PNG files across the static asset directory."""
        asset_dir = str(settings.ASSET_DIR)
        logger.debug(f"Walking asset directory for textures: {asset_dir}")
        for root, _, files in os.walk(asset_dir):
            for file in files:
                if file.endswith('.png'):
                    asset_key = file[:-4]
                    filepath = os.path.join(root, file)
                    logger.debug(f"Caching texture from {filepath} as '{asset_key}'")
                    self._textures[asset_key] = self.load(filepath)

    def _assemble(self):
        """Compiles composite characters utilizing cython-wrapped base and feature renders."""
        logger.debug("Assembling Persona stacks...")
        if not self.properties.get('sheets', None):
            return

        for cat in [AssetInstances.PIXIES, AssetInstances.SPRITES]:
            sheet = self.properties["sheets"].get(cat, None)
            
            if not sheet: continue

            for p_key, persona in sheet.get("personas", {}).items():
                stack = persona.get("stack", [])
                
                if not stack: continue

                base_key = persona.get("stack", [])[0]
                base_ptr = self._textures.get(base_key)

                if not base_ptr: continue
                
                stack_ptrs = []
                for f_key in stack[1:]:
                    if f_key in self._textures:
                        stack_ptrs.append(self._textures[f_key])

                if stack_ptrs:
                    logger.debug(f"Composing layered TexturePtr for Persona: '{p_key}'")
                    self._textures[p_key] = render.compose(base_ptr, stack_ptrs)
                else:
                    self._textures[p_key] = base_ptr

    def _index(self):
        """Maps runtime dynamic frame keys to their GPU mapping tuple coordinates."""
        logger.debug("Indexing Frame Keys to Texture Crops...")
        for cat_name, cat_props in self.properties.items():
            if not cat_props: continue
            
            cat_recipes = self.recipes.get(cat_name, None)
            
            if not cat_recipes: continue
            
            # Iterate through the Pydantic PyRecipe model fields
            for inst_name, recipe in cat_recipes:
                if not recipe: continue

                inst_props = cat_props.get(inst_name)
                if not inst_props: continue

                # 1. SingleFrame 
                if recipe.frame == FrameRecipe.SINGLE:

                    # Tiles schema has a list of keys; others map key -> properties
                    if cat_name == AssetCategories.TILES:
                        w, l = inst_props["dimensions"]["w"], inst_props["dimensions"]["l"]
                        for id in inst_props["ids"]:
                            if id in self._textures:
                                logger.debug(f"Indexed SingleFrame tile: '{id}'")
                                self._frames[id] = (self._textures[id], 0, 0, w, l)
                    else:
                        for id, props in inst_props.items():
                            if id in self._textures:
                                logger.debug(f"Indexed SingleFrame object: '{id}'")
                                w, l = props["dimensions"]["w"], props["dimensions"]["l"]
                                self._frames[id] = (self._textures[id], 0, 0, w, l)

                # 2. IterableFrame
                elif recipe.frame == FrameRecipe.ITERABLE:
                    for key, props in inst_props.items():
                        if key not in self._textures: continue
                        
                        w, l = props["dimensions"]["w"], props["dimensions"]["l"]
                        
                        # Differentiate between Binary Objects and Sequential Effects
                        if recipe.animation == AnimationRecipe.BINARY:
                            logger.debug(f"Indexed Binary IterableFrame: '{key}'")
                            self._frames[f"{key}-{settings.OFF}"] = (self._textures[key], 0, 0, w, l)
                            self._frames[f"{key}-{settings.ON}"] = (self._textures[key], w, 0, w, l)
                        else:
                            logger.debug(f"Indexed Sequential IterableFrame: '{key}' ({props['count']} frames)")
                            for f in range(props["count"]):
                                self._frames[f"{key}-{f}"] = (self._textures[key], f * w, 0, w, l)

                # 3. StateFrame (Sheets)
                elif recipe.frame == FrameRecipe.STATE:
                    for p_key, persona in inst_props["personas"].items():
                        if p_key not in self._textures: continue

                        w, l = persona["dimensions"]["w"], persona["dimensions"]["l"]
                        
                        for action, action_prop in inst_props["actions"].items():
                            for direction, dir_prop in action_prop["directions"].items():
                                row = dir_prop["row"]
                                for f in range(action_prop["count"]):
                                    frame_key = f"{p_key}-{action}-{direction}-{f}"
                                    logger.debug(f"Indexed StateFrame: '{frame_key}'")
                                    self._frames[frame_key] = (
                                        self._textures[p_key], f * w, row * l, w, l
                                    )

    def load(self, filepath: str) -> TexturePtr:
        """Loads a physical .png file directly into GPU memory via SDL2 extensions."""
        cdef bytes b_filepath = filepath.encode('utf-8')
        cdef SDL_Texture* tex = IMG_LoadTexture(_renderer, b_filepath)
        
        if tex == NULL:
            raise RuntimeError(f"Failed to load texture into GPU memory: {filepath}")

        cdef int w, l
        SDL_QueryTexture(tex, NULL, NULL, &w, &l)

        cdef TexturePtr wrapper = TexturePtr()
        wrapper.ptr = tex
        wrapper.w = w
        wrapper.l = l
        return wrapper
        
    def data(self, frame_key: str) -> Tuple:
        """
        Returns a lightweight Python tuple resolving mapped texture configurations for the camera.
        Format: (TexturePtr, src_x, src_y, src_w, src_l)
        """
        logger.debug(f"Querying registry for frame_key: '{frame_key}'")
        
        if frame_key in self._frames:
            logger.debug(f" -> Hit identified in precomputed _frames mapping.")
            return self._frames[frame_key]
            
        # Fallback for single-frame immutables like Tiles where schema crop === texture bounds
        if frame_key in self._textures:
            logger.debug(f" -> Hit identified in raw _textures mapping (fallback).")
            tex = self._textures[frame_key]
            return (tex, 0, 0, tex.w, tex.l)
            
        logger.debug(f" -> MISS: Frame key '{frame_key}' not found.")
        return None