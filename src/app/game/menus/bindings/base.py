"""
@domain.abstract
@app.base
@app.menu
@menu.binding

# Ontology: Source - app.game.menus.bindings.base

Abstract interface for binding Widget States to Asset State.
"""
# Standard Libraries
import functools
from abc import (
    ABC, 
    abstractmethod
)
from typing import (
    Any, 
    Tuple, 
    Optional
)

# Application Libraries
from app.models.menus import MenuContext
from app.models.config.menus import BindingTarget

class Binding(ABC):
    """
    Base interface for Menu bindings.
    """
    target: BindingTarget

    def __init__(self, target: BindingTarget, context: MenuContext, **kwargs):
        self.target = target
        self.context = context

    @staticmethod
    def _resolve_path(bind_path: str, context: MenuContext) -> Tuple[Any, Optional[str]]:
        """Resolves a dot-delimited context path into a (parent, attribute) tuple."""
        parts = bind_path.split(".")
        if parts and parts[0] == "context":
            parts = parts[1:]
        if not parts:
            return None, None

        try:
            parent = functools.reduce(
                lambda obj, attr: (
                    obj.get(attr) if isinstance(obj, dict) else getattr(obj, attr)
                ) if obj is not None else None,
                parts[:-1],
                context,
            )
            return parent, parts[-1]
        except AttributeError:
            return None, None

    @staticmethod
    def _deref(ref: Tuple[Any, Optional[str]], default: Any = None) -> Any:
        """Evaluates a pre-resolved (parent, attribute) tuple."""
        parent, attr = ref
        if parent is None or attr is None:
            return default
        if isinstance(parent, dict):
            return parent.get(attr, default)
        return getattr(parent, attr, default)

    @abstractmethod
    def bind(self, **kwargs) -> Any:
        pass