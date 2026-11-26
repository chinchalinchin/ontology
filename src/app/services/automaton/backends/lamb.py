"""
@domain.automata
@domain.concrete
@app.service

# Ontology: Source - app.services.automaton.backends.lamb

Lambda ConditionBackend implementation for ISL compilation and evaluation.
"""
# Standard Libraries
import logging
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    Sequence
)

# Application Libraries
import app.static.settings as settings
from app.services.automaton.base import Backend
from app.services.automaton.environ import Environ

# ----------------------------------------------

logger = logging.getLogger(__name__)

# ----------------------------------------------


class Lambda(Backend):
    """
    Lambda-backed ISL condition compiler and evaluator using settings.LAMBDA_SIGNATURE.
    """
    env_globals: Dict[str, Any]

    def __init__(self, env_globals: Optional[Dict[str, Any]] = None):
        self.env_globals = (
            env_globals if env_globals is not None else Environ.globals()
        )

    def conditionalize(self, condition: str) -> Callable[..., bool]:
        if not isinstance(condition, str):
            raise TypeError(
                f"ISL lambda condition must be a string; got {type(condition).__name__}."
            )
        try:
            # Validate raw expression syntax for strict AST/Lambda parity (B069)
            compile(condition, '<string>', 'eval')
            # Dynamic parameter list accommodates any dict passed via **locals
            func_str = settings.LAMBDA_SIGNATURE.format(cond=condition)
            compiled_func = eval(func_str, self.env_globals)
            if not callable(compiled_func):
                raise SyntaxError(
                    f"ISL lambda condition did not evaluate to a callable: '{condition}'"
                )
            return compiled_func
        except Exception as e:
            logger.error(f"Failed to compile ISL lambda condition '{condition}': {e}")
            raise

    def evaluate(
        self,
        conditions: Sequence[Any],
        locals: Dict[str, Any]
    ) -> bool:
        if not conditions:
            return False

        for condition in conditions:
            try:
                # Execute the lambda callable, unpacking the dynamic dictionary
                if not condition(**locals):
                    return False
            except AttributeError as e:
                logger.debug(f"ISL Lambda Evaluation Short-Circuit: {e}")
                return False

        return True