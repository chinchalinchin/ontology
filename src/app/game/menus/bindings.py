"""
# Ontology: app.game.menus.bindings

Formalizes Widget Bindings as ECS Components.
"""
# Standard Libraries
import functools
from abc import ABC, abstractmethod
from typing import Callable, Any, Tuple, List

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


class Binding(ABC):
    """
    Base Component for associating live game state with UI Widgets.
    """
    def __init__(self, target: str, context: dict, **kwargs):
        self.context = context
        self.parent, self.attr = self._resolve(target, context)
        
        # Guaranteed attributes for duck-typed MenuControllers
        self.selection = kwargs.get('selection')
        self.selector = kwargs.get('selector')

    def _resolve(self, bind_path: str, context: dict) -> Tuple[Any, str]:
        """Resolves a string path into a (parent, attribute) tuple securely once at init."""
        if not bind_path:
            return None, None
            
        parts = bind_path.split('.')
        if parts[0] == 'context':
            parts = parts[1:]
            
        if not parts:
            return None, None
            
        try:
            parent = functools.reduce(
                lambda obj, attr: (obj.get(attr) if isinstance(obj, dict) else getattr(obj, attr)) if obj is not None else None,
                parts[:-1],
                context
            )
            return parent, parts[-1]
        except AttributeError:
            return None, None

    def _get(self, default: Any = None) -> Any:
        """Safely extracts the resolved value from dictionaries or objects."""
        if self.parent is None or self.attr is None:
            return default
        if isinstance(self.parent, dict):
            return self.parent.get(self.attr, default)
        return getattr(self.parent, self.attr, default)

    @abstractmethod
    def bind(self, **kwargs) -> Tuple[Callable, ...]:
        """Returns the closures injected into the Widget's active State."""
        pass


class LibraryBinding(Binding):
    def __init__(self, target: str, context: dict, **kwargs):
        super().__init__(target, context, **kwargs)
        self.registry = kwargs.get('registry')
        self.library = kwargs.get('library')
        
        # BUG B005 Remediation: Cache localized to the Component instance
        self._cached_pages = None
        
    def bind(self, **kwargs) -> Tuple[Callable, ...]:
        w = kwargs.get('w', 0)
        l = kwargs.get('l', 0)
        
        def content_function():
            if self._cached_pages is not None:
                return self._cached_pages
            
            target_state = self._get()
            
            plot = getattr(target_state, 'plot', self.context.get('plot')) \
                    if target_state else self.context.get('plot')
            persona = getattr(target_state, 'persona', self.context.get('persona')) \
                    if target_state else self.context.get('persona')
            lexicon = getattr(target_state, 'lexicon', self.context.get('lexicon')) \
                    if target_state else self.context.get('lexicon')
            
            if hasattr(plot, 'current'):
                plot = plot.current
            elif isinstance(plot, dict):
                plot = plot.get('current')
                
            raw = self.library.fetch(plot, persona, lexicon) if self.library else ""
            font = self.registry.font("dialogue") if self.registry else None
            
            self._cached_pages = paginate(str(raw), font, w, l)
            return self._cached_pages
            
        return (content_function,)


class TextBinding(Binding):
    def __init__(self, target: str, context: dict, **kwargs):
        super().__init__(target, context, **kwargs)
        self.registry = kwargs.get('registry')
        self._cached_pages = None
        
    def bind(self, **kwargs) -> Tuple[Callable, ...]:
        w = kwargs.get('w', 0)
        l = kwargs.get('l', 0)
        
        def content_function():
            if self._cached_pages is not None:
                return self._cached_pages
                
            raw = self._get("")
            font = self.registry.font("dialogue") if self.registry else None
            
            self._cached_pages = paginate(str(raw), font, w, l)
            return self._cached_pages
            
        return (content_function,)


class MeterBinding(Binding):
    def bind(self, **kwargs) -> Tuple[Callable, ...]:
        def reading_function():
            target_state = self._get()
            return getattr(target_state, 'current', target_state) if target_state is not None else 0
            
        def unit_function():
            target_state = self._get()
            return getattr(target_state, 'maximum', 1) if target_state is not None else 1
            
        return (reading_function, unit_function)


class IconBinding(Binding):
    def bind(self, **kwargs) -> Tuple[Callable, ...]:
        def icon_function():
            return self._get("")
        return (icon_function,)


class SelectBinding(Binding):
    def bind(self, **kwargs) -> Tuple[Callable, ...]:
        return ()