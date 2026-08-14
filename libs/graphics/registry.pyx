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
import app.config.settings as settings
from app.hooks.factory import Factory

# Cython Libraries
from libs.graphics.render cimport (
    _renderer, 
    SDL_Renderer, 
    SDL_Texture, 
    SDL_DestroyTexture, 
    SDL_QueryTexture
)
import libs.graphics.render as render

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
    # Public Fields
    properties: dict
    recipes: dict
    # Hidden Fields
    _textures: dict
    _frames: dict
    
    def __init__(self, properties, recipes):
        logger.debug("Initializing Asset Registry...")
        self._textures = {}
        self._frames = {}
        self.properties = properties
        self.recipes = recipes

        self._cache()
        self._stack()
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

    def _extract(self, inst_props):
        """Helper to agnostically extract property items from schema variations."""
        if not isinstance(inst_props, dict):
            return
        if "personas" in inst_props:
            for k, v in inst_props["personas"].items():
                yield k, {**v, "actions": inst_props.get("actions", {})}
        elif "ids" in inst_props:
            for k in inst_props["ids"]:
                yield k, inst_props
        else:
            for k, v in inst_props.items():
                if isinstance(v, dict):
                    yield k, v

    def _stack(self):
        """Data-Driven Texture Assembly."""
        logger.debug("Assembling Texture Stacks...")
        for _, cat_props in self.properties.items():
            if not cat_props: continue
            for _, inst_props in cat_props.items():
                for item_id, item_props in self._extract(inst_props):
                    stack = item_props.get("stack", [])
                    if not stack: continue

                    base_key = stack[0]
                    base_ptr = self._textures.get(base_key)
                    if not base_ptr: continue
                    
                    stack_ptrs = []
                    for f_key in stack[1:]:
                        if f_key in self._textures:
                            stack_ptrs.append(self._textures[f_key])

                    if stack_ptrs:
                        logger.debug(f"Composing layered TexturePtr for: '{item_id}'")
                        self._textures[item_id] = render.compose(base_ptr, stack_ptrs)
                    else:
                        self._textures[item_id] = base_ptr

    def _index(self):
        """Maps runtime dynamic frame keys to their GPU mapping tuple coordinates."""
        logger.debug("Indexing Frame Keys to Texture Crops...")
        for cat_name, cat_props in self.properties.items():
            if not cat_props: continue
            
            cat_recipes = self.recipes.get(cat_name)
            if not cat_recipes: continue
            
            for inst_name, recipe in cat_recipes.items():
                if not recipe: continue

                inst_props = cat_props.get(inst_name)
                if not inst_props: continue

                frame_worker = Factory.frame(recipe["frame"])
                for item_id, item_props in self._extract(inst_props):
                    
                    if item_id not in self._textures: continue
                    
                    crop_map = frame_worker.index(item_id, item_props)
                    for frame_key, crop in crop_map.items():
                        logger.debug(f"Indexed frame: '{frame_key}'")
                        self._frames[frame_key] = (
                            self._textures[item_id], 
                            crop[0], crop[1], crop[2], crop[3]
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