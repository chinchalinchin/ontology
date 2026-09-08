"""
# Ontology: app.game.menus.bindings.library

Library Widget Binding implementation.
"""
# Standard Libraries
from typing import Callable,Tuple

# Application Libraries
from app.game.menus.contexts import MenuContext
from app.game.menus.bindings.base import Binding

# Cython Libraries
import libs.graphics.render as render

def paginate(text: str, font: Any, w: int, l: int) -> List[str]:
    """Shared utility for formatting text into wrapped pages."""
    if not text or not font:
        return [str(text)] if text else [""]
        
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
    def __init__(self, target: dict, context: MenuContext, **kwargs):
        super().__init__(target, context, **kwargs)
        self.registry = kwargs.get('registry')
        self.library = kwargs.get('library')
        self._cached_pages = None
        
    def bind(self, **kwargs) -> Tuple[Callable, ...]:
        w, l = kwargs.get('w', 0), kwargs.get('l', 0)
        
        def content_function():
            if self._cached_pages is not None:
                return self._cached_pages
            
            plot = self._get('plot', "")
            persona = self._get('persona', "")
            lexicon = self._get('lexicon', "")
                
            raw = self.library.fetch(plot, persona, lexicon) if self.library else ""
            font = self.registry.font("dialogue") if self.registry else None
            
            self._cached_pages = paginate(str(raw), font, w, l)
            return self._cached_pages
            
        return (content_function,)

class TextBinding(Binding):
    def __init__(self, target: dict, context: MenuContext, **kwargs):
        super().__init__(target, context, **kwargs)
        self.registry = kwargs.get('registry')
        self._cached_pages = None
        
    def bind(self, **kwargs) -> Tuple[Callable, ...]:
        w, l = kwargs.get('w', 0), kwargs.get('l', 0)
        
        def content_function():
            if self._cached_pages is not None:
                return self._cached_pages
                
            raw = self._get('content', "")
            font = self.registry.font("dialogue") if self.registry else None
            
            self._cached_pages = paginate(str(raw), font, w, l)
            return self._cached_pages
            
        return (content_function,)