"""
@domain.automata
@domain.concrete
@app.service

# Ontology: Source - app.services.translators.compiler

AST ConditionBackend implementation for ISL compilation and evaluation.
"""
# Standard Libraries
import logging
from typing import (
    Any,
    Dict,
    Optional,
    Sequence
)

# Application Libraries
from app.services.translators.base import Backend
from app.services.translators.environ import Environ

logger = logging.getLogger(__name__)


class Compiler(Backend):
    """
    AST-backed ISL condition compiler and evaluator using Python compile()/eval().
    """
    env_globals: Dict[str, Any]

    def __init__(self, env_globals: Optional[Dict[str, Any]] = None):
        # Construct the globals dictionary once
        self.env_globals = (
            env_globals if env_globals is not None else Environ.globals()
        )

    def conditionalize(self, condition: str) -> Any:
        if not isinstance(condition, str):
            raise TypeError(
                f"ISL AST condition must be a string; got {type(condition).__name__}."
            )
        try:
            return compile(condition, '<string>', 'eval')
        except Exception as e:
            logger.error(f"Failed to compile ISL AST condition '{condition}': {e}")
            raise

    def evaluate(
        self,
        conditions: Sequence[Any],
        locals: Dict[str, Any]
    ) -> bool:
        if not conditions:
            return False

        for code_obj in conditions:
            try:
                # Evaluate the compiled AST object using the cached globals and dynamic locals
                if not eval(code_obj, self.env_globals, locals):
                    return False
            except AttributeError as e:
                logger.debug(f"ISL AST Evaluation Short-Circuit: {e}")
                return False

        return True