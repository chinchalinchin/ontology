"""
# Ontology: app.services.translators.base

Defines the foundational interfaces for Intentional Scripting Language (ISL) compilation 
and execution within the game engine.
"""
# Standard Libraries
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

@dataclass(slots=True)
class Transition:
    """
    Dynamic game model representing a compiled transition rule.
    """
    next: str
    conditions: List[Any]  # Can hold Callables (Lambdas) or CodeType objects (AST)

class Executor(ABC):
    """
    Defines the execution contract for evaluating intention/plot transitions.
    """
    transitions: Dict[str, List[Transition]]
    
    def __init__(self, transitions: Dict[str, List[Transition]]):
        self.transitions = transitions

    @abstractmethod
    def evaluate(self, current_state: str, locals: Dict[str, Any]) -> Optional[str]:
        """
        Evaluates the dynamic locals against the compiled ISL conditions for a given state.
        
        Returns the string key for the next valid state transition, 
        or None if no transitions evaluate to True.
        """
        pass


class Translator(ABC):
    """
    Defines the compilation contract for translating raw ISL string rules into 
    executable components.
    """
    
    @abstractmethod
    def compile(self, raw_configs: Dict[str, List[Any]]) -> Executor:
        """
        Compiles string conditions into Python executables and constructs an Executor 
        capable of evaluating them at runtime.
        """
        pass