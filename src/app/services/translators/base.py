"""
# Ontology: app.services.translators.base

Defines the foundational interfaces for Intentional Scripting Language (ISL) compilation 
and execution within the game engine.
"""
# Standard Libraries
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

# Application Libraries
from app.models.state import SpriteState
from app.config.enums import Intentions
from app.models.config import IntentionConfiguration

@dataclass(slots=True)
class IntentionTransition:
    """
    Dynamic game model representing a compiled transition rule.
    """
    next: Intentions
    conditions: List[Any]  # Can hold Callables (Lambdas) or CodeType objects (AST)

class Executor(ABC):
    """
    Defines the execution contract for evaluating intention transitions.
    """
    transitions: Dict[Intentions, List[IntentionTransition]]
    
    def __init__(self, transitions: Dict[Intentions, List[IntentionTransition]]):
        self.transitions = transitions

    @abstractmethod
    def evaluate(self, sprite: SpriteState, sprites: Dict[str, Any]) -> Optional[Intentions]:
        """
        Evaluates the Sprite's state against the compiled ISL conditions.
        
        Returns the Intentions enum key for the next valid state transition, 
        or None if no transitions evaluate to True.
        """
        pass


class Translator(ABC):
    """
    Defines the compilation contract for translating raw ISL string rules into 
    executable components.
    """
    
    @abstractmethod
    def compile(self, raw_intentions: Dict[str, List[IntentionConfiguration]]) -> Executor:
        """
        Compiles string conditions into Python executables and constructs an Executor 
        capable of evaluating them at runtime.
        """
        pass