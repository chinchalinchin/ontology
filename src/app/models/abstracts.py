"""
@domain.abstract

# Ontology: Source - app.assets.base

Base Asset Interfaces.
"""
# Standard Libraries
from abc import ABC
from typing import (
    Dict,
    Type,
    Any
)

class Singleton(ABC):
    _instances: Dict[Type[Any], Any] = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]
