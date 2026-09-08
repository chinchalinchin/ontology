"""
# Ontology: app.game.menus.bindings

Package for binding Widget states to game state.
"""
# Standard Libraries
import functools
from abc import ABC, abstractmethod
from typing import Callable, Any, Tuple, Dict

# Application Libraries
from app.game.menus.contexts import MenuContext


class Binding(ABC):
    """
    Base Component for associating live game state with UI Widgets.
    """
    def __init__(self, target: dict, context: MenuContext, **kwargs):
        self.context = context
        self.target = target or {}
        self.resolved: Dict[str, Tuple[Any, str]] = {}
        
        # Pre-resolve all context paths in the target dictionary
        for key, val in self.target.items():
            # Skip literal strings used in SelectBindings
            if not isinstance(val, str) or not val.startswith('context.'):
                continue
            self.resolved[key] = self._resolve(val, context)
        
        # Guaranteed attributes for duck-typed MenuControllers
        self.selection = self.target.get('selection')
        self.selector = self.target.get('selector')

    def _resolve(self, bind_path: str, context: MenuContext) -> Tuple[Any, str]:
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
                lambda obj, attr: (obj.get(attr) 
                                    if isinstance(obj, dict) 
                                    else getattr(obj, attr)) 
                                        if obj is not None 
                                        else None,
                parts[:-1],
                context
            )
            return parent, parts[-1]
        except AttributeError:
            return None, None

    def _get(self, key: str, default: Any = None) -> Any:
        """Safely extracts the resolved value based on the target key."""
        parent, attr = self.resolved.get(key, (None, None))
        if parent is None or attr is None:
            return default
        if isinstance(parent, dict):
            return parent.get(attr, default)
        return getattr(parent, attr, default)

    @abstractmethod
    def bind(self, **kwargs) -> Tuple[Callable, ...]:
        pass