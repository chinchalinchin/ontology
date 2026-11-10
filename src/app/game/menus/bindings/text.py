"""
@domain.concrete
@domain.user
@app.menu
@menu.binding


# Ontology: Source - app.game.menus.bindings.library

Library Widget Binding implementation.
"""
from __future__ import annotations

# Standard Libraries
from typing import (
    Callable, 
    Tuple, 
    Any, 
    List,
    TYPE_CHECKING
)

# Application Libraries
from app.game.menus.bindings.base import Binding
from app.models.config.menus import (
    LibraryTarget,
    TextTarget
)
from app.models.menus.contexts import MenuContext

if TYPE_CHECKING:
    from app.services.generators.menus.library import Library

# Cython Libraries
## NOTE: Uneasy about importing the SDL interface here. 
##       I don't see any other way of measuring the font, though.
##       Research should be done into alternate implementations
##       that don't require over-complicating the application
##       dependency tree.
import libs.graphics.render as render
from libs.graphics.registry import Registry


# ------------------------------------------------------------------------------

def paginate(text: str, font: Any, w: int, l: int) -> List[str]:
    """Shared utility for formatting text into wrapped pages."""
    if not text or not font:
        return [str(text)] if text else [""]

    # TODO: need to type `font` and get rid of duck-typing.
    margin_w = int(w * font.margins) if hasattr(font, 'margins') else 0
    margin_l = int(l * font.margins) if hasattr(font, 'margins') else 0
    
    wrap_width = w - (2 * margin_w)
    wrap_height = l - (2 * margin_l)
    
    if wrap_width <= 0 or wrap_height <= 0:
        return [text]
        
    words = text.split(' ')
    lines = []
    current_line = ""
    
    for word in words:
        test_line = f"{current_line} {word}".strip() if current_line else word
        tw, th = render.measure(test_line, font)
        
        if tw > wrap_width and current_line:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test_line
            
    if current_line:
        lines.append(current_line)
        
    if not lines:
        return [""]
        
    _, line_height = render.measure(lines[0], font)
    line_height = max(line_height, 10)
        
    max_lines_per_page = max(1, wrap_height // line_height)
    
    pages = []
    for i in range(0, len(lines), max_lines_per_page):
        page_lines = lines[i : i + max_lines_per_page]
        pages.append("\n".join(page_lines))
        
    return pages



class LibraryBinding(Binding):
    """
    """
    
    target: LibraryTarget

    def __init__(self, 
        target: LibraryTarget, 
        context: MenuContext, 
        library: Library = None, 
        registry: Registry = None, 
        **kwargs
    ):
        super().__init__(target, context, **kwargs)
        self.library = library
        self.registry = registry
        self._cached_pages = None
        self._plot_ref = self._resolve_path(target.plot, context)
        self._persona_ref = self._resolve_path(target.persona, context)
        self._lexicon_ref = self._resolve_path(target.lexicon, context)
        
    def bind(self, **kwargs) -> Tuple[Callable, ...]:
        """
        """
        w, l = kwargs.get('w', 0), kwargs.get('l', 0)
        
        def content_function():
            if self._cached_pages is not None:
                return self._cached_pages
            
            plot = self._deref(self._plot_ref)
            persona = self._deref(self._persona_ref)
            lexicon = self._deref(self._lexicon_ref)
                
            raw = self.library.fetch(plot, persona, lexicon) if self.library else ""
            font = self.registry.font("dialogue") if self.registry else None
            
            self._cached_pages = paginate(str(raw), font, w, l)
            return self._cached_pages
            
        return content_function


class TextBinding(Binding):
    target: TextTarget

    def __init__(self, 
        target: TextTarget, 
        context: MenuContext, 
        registry: Registry = None, 
        **kwargs
    ):
        super().__init__(target, context, **kwargs)
        self.registry = registry
        self._cached_pages = None

    def bind(self, **kwargs) -> Tuple[Callable, ...]:
        w, l = kwargs.get('w', 0), kwargs.get('l', 0)
        
        def content_function():
            if self._cached_pages is not None:
                return self._cached_pages
                
            raw = self.target.content
            font = self.registry.font("dialogue") if self.registry else None
            
            self._cached_pages = paginate(str(raw), font, w, l)
            return self._cached_pages
            
        return content_function