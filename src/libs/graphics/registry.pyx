# cython: language_level=3
"""
# Ontology: libs.graphics.registry
"""
# Standard Libraries
import os
import time
import logging

# Application Libraries
import app.config.settings as settings

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
    def __dealloc__(self):
        if self.ptr != NULL:
            SDL_DestroyTexture(self.ptr)
            self.ptr = NULL

cdef class TTFFont:
    def __dealloc__(self):
        if self.ptr != NULL:
            TTF_CloseFont(self.ptr)
            self.ptr = NULL

def _sys_load_image(filepath: str):
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

def _sys_load_font(filepath: str, pt_size: int, style: dict):
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

cdef class Registry:
    cdef public dict properties
    cdef public dict recipes
    cdef public dict typography

    cdef public dict _textures
    cdef public dict _frames
    cdef public dict _fonts
    cdef public dict _filepaths
    cdef public dict _stacks
    cdef public list _pending_assets
    cdef public int maximum
    cdef public int current

    def __init__(self, dict properties, dict recipes, dict typography=None):
        if typography is None:
            typography = {}
            
        logger.debug("Initializing Asset Registry...")
        self._textures = {}
        self._frames = {}
        self._fonts = {}
        self._filepaths = {}
        self._stacks = {}
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

    def _get_or_load_texture(self, asset_key: str, bint raw_only=False):
        if not raw_only and asset_key in self._textures:
            return self._textures[asset_key]
            
        # 1. Virtual Stack Resolution
        if not raw_only and asset_key in self._stacks:
            stack = self._stacks[asset_key]
            
            # If a stack component references the parent key, force a physical 
            # load to break the cyclic dependency and prevent a C-stack overflow.
            base_key = stack[0]
            force_raw = (base_key == asset_key)
            base_ptr = self._get_or_load_texture(base_key, raw_only=force_raw)
            
            if not base_ptr: return None
            
            stack_ptrs = []
            for f_key in stack[1:]:
                f_force_raw = (f_key == asset_key)
                f_ptr = self._get_or_load_texture(f_key, raw_only=f_force_raw)
                if f_ptr: stack_ptrs.append(f_ptr)
                
            tex = render.compose(base_ptr, stack_ptrs) if stack_ptrs else base_ptr
            self._textures[asset_key] = tex
            return tex

        # 2. Physical File Resolution
        filepath = self._filepaths.get(asset_key)
        if filepath and filepath.endswith('.png'):
            tex = self._load_image(filepath)
            # Prevent intermediate raw textures from polluting the composited cache
            if not raw_only and tex: 
                self._textures[asset_key] = tex
            return tex
            
        return None

    def _load_image(self, filepath: str):
        return _sys_load_image(filepath)

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
        if font_key not in self.typography:
            return None
            
        cdef dict style = self.typography[font_key]
        cdef int pt_size = style.get("size", 24)
        return _sys_load_font(filepath, pt_size, style)

    def _extract(self, inst_props):
        if not isinstance(inst_props, dict): return
        else:
            for k, v in inst_props.items():
                if isinstance(v, dict): yield k, v

    def _stack(self):
        logger.debug("Registering Texture Stacks dependencies...")
        for _, cat_props in self.properties.items():
            if not cat_props: continue
            for _, inst_props in cat_props.items():
                for item_id, item_props in self._extract(inst_props):
                    stack = item_props.get("stack", [])
                    if not stack: continue
                    self._stacks[item_id] = stack
                    if item_id not in self._pending_assets:
                        self._pending_assets.append(item_id)
                        self.maximum += 1

    def _index(self):
        from app.services.orchestration.factory import Factory

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
                    if item_id not in self._filepaths and item_id not in self._stacks: 
                        continue
                    crop_map = frame_worker.index(item_id, item_props)
                    for frame_key, crop in crop_map.items():
                        self._frames[frame_key] = (item_id, crop[0], crop[1], crop[2], crop[3])

    def image(self, frame_key: str) -> tuple:
        if frame_key in self._frames:
            item_id, sx, sy, sw, sl = self._frames[frame_key]
            tex = self._get_or_load_texture(item_id)
            if tex: return (tex, sx, sy, sw, sl)
            
        if frame_key in self._filepaths or frame_key in self._stacks:
            tex = self._get_or_load_texture(frame_key)
            if tex: return (tex, 0, 0, tex.w, tex.l)
            
        return None

    def font(self, font_key: str):
        return self._get_or_load_font(font_key)
        
    def prewarm(self, budget_ms: int) -> bool:
        start = time.perf_counter()
        while self._pending_assets:
            if (time.perf_counter() - start) * 1000 > budget_ms:
                return False
                
            asset_key = self._pending_assets.pop()
            self._get_or_load_texture(asset_key)
            self._get_or_load_font(asset_key)
            self.current += 1
            
        return True