# cython: language_level=3
"""
# Ontology: libs.graphics.registry
"""
# Standard Libraries
import os
import time
import logging
import dataclasses

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

# -------------------------------------------------------------------------------

cdef extern from "SDL2/SDL_image.h":
    SDL_Texture* IMG_LoadTexture(SDL_Renderer* renderer, const char* file)
    
cdef extern from "SDL2/SDL_ttf.h":
    int TTF_STYLE_NORMAL
    int TTF_STYLE_BOLD
    int TTF_STYLE_ITALIC
    int TTF_STYLE_UNDERLINE
    int TTF_STYLE_STRIKETHROUGH
    void TTF_SetFontStyle(TTF_Font* font, int style)
    void TTF_SetFontOutline(TTF_Font* font, int outline)

    int TTF_WasInit()
    TTF_Font* TTF_OpenFont(const char* file, int ptsize)
    void TTF_CloseFont(TTF_Font* font)

# -------------------------------------------------------------------------------

cdef class TexturePtr:
    def __dealloc__(self):
        # B008 Fix: Prevent deallocation against torn-down SDL driver
        if self.ptr != NULL:
            if _renderer != NULL:
                SDL_DestroyTexture(self.ptr)
            self.ptr = NULL

cdef class TTFFont:
    def __dealloc__(self):
        # Prevent closing font if TTF subsystem is already terminated
        if TTF_WasInit():
            if self.ptr != NULL:
                TTF_CloseFont(self.ptr)
                self.ptr = NULL
            if self.outline_ptr != NULL:
                TTF_CloseFont(self.outline_ptr)
                self.outline_ptr = NULL

# -------------------------------------------------------------------------------

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

def _sys_load_font(filepath: str, object style):
    cdef int pt_size = style.size
    cdef bytes b_filepath = filepath.encode('utf-8')
    cdef TTF_Font* f_ptr = TTF_OpenFont(b_filepath, pt_size)
    cdef int sdl_style = TTF_STYLE_NORMAL
    cdef TTFFont font_obj
    cdef int outline_width = 0

    if f_ptr == NULL:
        raise RuntimeError(f"Failed to load font into memory: {filepath}")

    if style.bold: sdl_style |= TTF_STYLE_BOLD
    if style.italics: sdl_style |= TTF_STYLE_ITALIC
    if style.underline: sdl_style |= TTF_STYLE_UNDERLINE
    if style.strikethrough: sdl_style |= TTF_STYLE_STRIKETHROUGH
    TTF_SetFontStyle(f_ptr, sdl_style)

    font_obj = TTFFont()
    font_obj.ptr = f_ptr
    font_obj.margins = style.margins
    font_obj.align_str = style.alignment.value

    font_obj.color.r = style.color.r
    font_obj.color.g = style.color.g
    font_obj.color.b = style.color.b
    font_obj.color.a = style.color.a

    font_obj.outline_ptr = NULL
    if style.outline is not None and style.outline.width > 0:
        outline_width = style.outline.width
        font_obj.outline_width = outline_width
        font_obj.outline_ptr = TTF_OpenFont(b_filepath, pt_size)
        if font_obj.outline_ptr != NULL:
            TTF_SetFontStyle(font_obj.outline_ptr, sdl_style)
            TTF_SetFontOutline(font_obj.outline_ptr, outline_width)
            font_obj.outline_color.r = style.outline.color.r
            font_obj.outline_color.g = style.outline.color.g
            font_obj.outline_color.b = style.outline.color.b
            font_obj.outline_color.a = style.outline.color.a
    else:
        font_obj.outline_width = 0

    return font_obj
    
# -------------------------------------------------------------------------------

cdef class Registry:
    cdef public object properties   # PropertiesSchema
    cdef public object recipes      # RecipeConfiguration
    cdef public dict typography     # Dict[str, FontProperties]

    cdef public dict _textures
    cdef public dict _frames
    cdef public dict _fonts
    cdef public dict _filepaths
    cdef public dict _stacks
    cdef public list _pending_assets
    cdef public int maximum
    cdef public int current

    def __init__(self, object properties, object recipes, dict typography=None):
        logger.debug("Initializing Asset Registry with native application models...")
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
        self.typography = typography if typography is not None else {}
        
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
            tex = self._load_texture(filepath)
            # Prevent intermediate raw textures from polluting the composited cache
            if not raw_only and tex: 
                self._textures[asset_key] = tex
            return tex
            
        return None


    def _load_texture(self, filepath: str):
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
        style = self.typography[font_key]
        return _sys_load_font(filepath, style)


    def _stack(self):
        """
        Extracts Sheet stack dependencies from SheetPropertyInstances.
        """
        logger.debug("Registering Texture Stacks dependencies from Sheet properties...")
        if not hasattr(self.properties, "sheets") or not self.properties.sheets:
            return

        for sheet_field in dataclasses.fields(self.properties.sheets):
            sheet_instances = getattr(self.properties.sheets, sheet_field.name, {})
            if not isinstance(sheet_instances, dict):
                continue
            for item_id, item_props in sheet_instances.items():
                stack = getattr(item_props, "stack", None)
                if not stack:
                    continue
                self._stacks[item_id] = stack
                if item_id not in self._pending_assets:
                    self._pending_assets.append(item_id)
                    self.maximum += 1


    def _index(self):
        """
        Indexes frame coordinates by mapping Category and Instance dataclass fields.
        """
        from app.services.generators.game.factory import Factory

        logger.debug("Indexing Frame Keys to Texture Crops using native data models...")
        for cat_field in dataclasses.fields(self.properties):
            cat_name = cat_field.name
            if cat_name == "fonts":
                continue

            cat_props = getattr(self.properties, cat_name, None)
            cat_recipes = getattr(self.recipes, cat_name, None)
            if not cat_props or not cat_recipes:
                continue

            for inst_field in dataclasses.fields(cat_props):
                inst_name = inst_field.name
                recipe = getattr(cat_recipes, inst_name, None)
                if not recipe:
                    continue

                inst_dict = getattr(cat_props, inst_name, {})
                if not inst_dict or not isinstance(inst_dict, dict):
                    continue

                frame_worker = Factory.frame(recipe.frame)
                for item_id, item_props in inst_dict.items():
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


    cpdef void clear(self):
        """
        Explicitly destroys and clears all cached GPU textures and font objects.
        """
        cdef TexturePtr tex
        cdef TTFFont font_obj

        for tex in list(self._textures.values()):
            if tex is not None and tex.ptr != NULL:
                if _renderer != NULL:
                    SDL_DestroyTexture(tex.ptr)
                tex.ptr = NULL
        self._textures.clear()

        for font_obj in list(self._fonts.values()):
            if font_obj is not None and font_obj.ptr != NULL:
                if TTF_WasInit():
                    TTF_CloseFont(font_obj.ptr)
                font_obj.ptr = NULL
        self._fonts.clear()

        self._frames.clear()
        self._stacks.clear()
        self._pending_assets.clear()