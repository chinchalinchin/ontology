# cython: language_level=3
"""
# Ontology: libs.graphics.registry

Cythonized extension for ingesting physical image files, tracking their GPU memory pointers and flat-mapping Frame keys directly to GPU texture croppings. 
"""
# Standard Libraries
import os
import time
import logging
from typing import Tuple

# Application Libraries
import app.config.settings as settings
from app.services.factory import Factory

# Cython Libraries
from libs.graphics.render cimport (
    _renderer, 
    SDL_Renderer, 
    SDL_Texture, 
    SDL_DestroyTexture, 
    SDL_QueryTexture
)
import libs.graphics.render as render

logger = logging.getLogger("libs.graphics.registry")

cdef extern from "SDL2/SDL_image.h":
    SDL_Texture* IMG_LoadTexture(SDL_Renderer* renderer, const char* file)
    
cdef extern from "SDL2/SDL_ttf.h":
    int TTF_STYLE_NORMAL
    int TTF_STYLE_BOLD
    int TTF_STYLE_ITALIC
    void TTF_SetFontStyle(TTF_Font* font, int style)

    TTF_Font* TTF_OpenFont(const char* file, int ptsize)
    void TTF_CloseFont(TTF_Font* font)

cdef class TexturePtr:
    """
    Cython extension type wrapping the raw C-pointer for an SDL_Texture.
    Provides automated memory leak prevention on pointer garbage collection.
    """
    def __dealloc__(self):
        if self.ptr != NULL:
            SDL_DestroyTexture(self.ptr)
            self.ptr = NULL

cdef class TTFFont:
    """
    Cython extension type wrapping the raw C-pointer for an TTF_Font.
    Provides automated memory leak prevention on pointer garbage collection.
    """
    
    def __dealloc__(self):
        if self.ptr != NULL:
            TTF_CloseFont(self.ptr)
            self.ptr = NULL

class Registry:
    """
    Centralized Asset Registry to ingest configuration, cache GPU textures, 
    and map dynamic string keys to crop coordinates.
    """
    
    properties: dict
    recipes: dict
    typography: dict

    cdef dict _textures
    cdef dict _frames
    cdef dict _fonts
    cdef public dict _filepaths
    cdef public list _pending_assets
    cdef public int maximum
    cdef public int current

    def __init__(self, properties, recipes, typography={}):
        logger.debug("Initializing Asset Registry...")
        self._textures = {}
        self._frames = {}
        self._fonts = {}
        self._filepaths = {}
        self._pending_assets = []
        self.maximum = 0
        self.current = 0
        self.properties = properties
        self.recipes = recipes
        self.typography = typography
        self._cache()
        self._stack()
        self._index()

    def _cache(self):
        """Recursively parses all physical PNG and TTF files across the static asset directory."""
        asset_dir = str(settings.ASSET_DIR)
        logger.debug(f"Walking asset directory for assets: {asset_dir}")
        for root, _, files in os.walk(asset_dir):
            for file in files:
                asset_key = file[:-4]
                filepath = os.path.join(root, file)

                if file.endswith('.png') or file.endswith('.ttf'):
                    self._filepaths[asset_key] = filepath
                    self._pending_assets.append(asset_key)
        self.maximum = len(self._pending_assets)
        self.current = 0

    def _get_or_load_texture(self, asset_key: str):
        if asset_key in self._textures:
            return self._textures[asset_key]
            
        filepath_or_stack = self._filepaths.get(asset_key)
        if not filepath_or_stack:
            return None
            
        if isinstance(filepath_or_stack, list):
            base_key = filepath_or_stack[0]
            base_ptr = self._get_or_load_texture(base_key)
            if not base_ptr: return None
            stack_ptrs = []
            for f_key in filepath_or_stack[1:]:
                f_ptr = self._get_or_load_texture(f_key)
                if f_ptr: stack_ptrs.append(f_ptr)
            tex = render.compose(base_ptr, stack_ptrs) if stack_ptrs else base_ptr
            self._textures[asset_key] = tex
            return tex
            
        if filepath_or_stack.endswith('.png'):
            tex = self._load_image(asset_key, filepath_or_stack)
            if tex: self._textures[asset_key] = tex
            return tex
        return None

    def _load_image(self, image_key, filepath: str) -> TexturePtr:
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

    def _get_or_load_font(self, font_key: str):
        if font_key in self._fonts:
            return self._fonts[font_key]
        filepath = self._filepaths.get(font_key)
        if filepath and filepath.endswith('.ttf'):
            font_obj = self._load_font(font_key, filepath)
            if font_obj: self._fonts[font_key] = font_obj
            return font_obj
        return None

    def _load_font(self, font_key: str, filepath: str):
        """Loads and pre-styles a .ttf file into memory based on its configuration block."""

        if font_key not in self.typography:
            return None
            
        cdef dict style = self.typography[font_key]
        cdef int pt_size = style.get("size", 24)
        cdef bytes b_filepath = filepath.encode('utf-8')
        
        cdef TTF_Font* f_ptr = TTF_OpenFont(b_filepath, pt_size)
        if f_ptr == NULL:
            raise RuntimeError(f"Failed to load font into memory: {filepath}")
            
        cdef int sdl_style = TTF_STYLE_NORMAL
        if style.get("bold", False): sdl_style |= TTF_STYLE_BOLD
        if style.get("italics", False): sdl_style |= TTF_STYLE_ITALIC
        TTF_SetFontStyle(f_ptr, sdl_style)
        
        cdef TTFFont font_obj = TTFFont()
        font_obj.ptr = f_ptr
        font_obj.margins = style.get("margins", 0.05)
        font_obj.align_str = style.get("alignment", "left")
        
        cdef dict color_cfg = style.get("color", {})
        font_obj.color.r = color_cfg.get("r", 255)
        font_obj.color.g = color_cfg.get("g", 255)
        font_obj.color.b = color_cfg.get("b", 255)
        font_obj.color.a = color_cfg.get("a", 255)
        
        return font_obj

    def _extract(self, inst_props):
        """Helper to agnostically extract property items from schema variations."""
        if not isinstance(inst_props, dict): return
        else:
            for k, v in inst_props.items():
                if isinstance(v, dict): yield k, v

    def _stack(self):
        """Data-Driven Texture Assembly."""
        logger.debug("Registering Texture Stacks dependencies...")
        for _, cat_props in self.properties.items():
            if not cat_props: continue
            for _, inst_props in cat_props.items():
                for item_id, item_props in self._extract(inst_props):
                    stack = item_props.get("stack", [])
                    if not stack: continue
                    self._filepaths[item_id] = stack
                    if item_id not in self._pending_assets:
                        self._pending_assets.append(item_id)
                        self.maximum += 1

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
                    if item_id not in self._filepaths: continue
                    crop_map = frame_worker.index(item_id, item_props)
                    if not crop_map:
                        logger.warning(f"[REGISTRY] Frame indexer {type(frame_worker).__name__} returned empty crop_map for '{item_id}'")
                    for frame_key, crop in crop_map.items():
                        logger.debug(f"Indexed frame: '{frame_key}'")
                        self._frames[frame_key] = (item_id, crop[0], crop[1], crop[2], crop[3])

    def image(self, frame_key: str) -> tuple:
        """
        Returns a lightweight Python tuple resolving mapped texture configurations for the camera.
        Format: (TexturePtr, src_x, src_y, src_w, src_l)
        """
        logger.debug(f"Querying registry for frame_key: '{frame_key}'")
        if frame_key in self._frames:
            item_id, sx, sy, sw, sl = self._frames[frame_key]
            tex = self._get_or_load_texture(item_id)
            if tex: return (tex, sx, sy, sw, sl)
        if frame_key in self._filepaths:
            val = self._filepaths[frame_key]
            if isinstance(val, list) or val.endswith('.png'):
                tex = self._get_or_load_texture(frame_key)
                if tex: return (tex, 0, 0, tex.w, tex.l)
        return None

    def font(self, font_key: str):
        """Returns the pre-configured TTFFont wrapper indexed during initialization."""
        return self._get_or_load_font(font_key)
        
    def prewarm(self, budget_ms: int) -> bool:
        start = time.perf_counter()
        while self._pending_assets:
            if (time.perf_counter() - start) * 1000 > budget_ms:
                return False
            asset_key = self._pending_assets.pop()
            val = self._filepaths.get(asset_key)
            if isinstance(val, list) or (isinstance(val, str) and val.endswith('.png')):
                self._get_or_load_texture(asset_key)
            elif isinstance(val, str) and val.endswith('.ttf'):
                self._get_or_load_font(asset_key)
            self.current += 1
        return True