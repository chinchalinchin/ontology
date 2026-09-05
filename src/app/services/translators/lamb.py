"""
# Ontology: app.services.translators.lamb
"""
# Standard Libraries
import logging
from types import SimpleNamespace
from typing import (
    Dict, 
    List,
    Optional, 
    Any, 
    Callable
)

# Application Libraries
from app.services.translators.base import (
    Translator, 
    Executor, 
    Transition
)
from app.services.translators.environ import Environ

logger = logging.getLogger(__name__)

class LambdaExecutor(Executor):
    def evaluate(self, current_state: str, locals: Dict[str, Any]) -> Optional[str]:
        if current_state not in self.transitions:
            return None
            
        for transition in self.transitions[current_state]:
            if not transition.conditions:
                continue
                
            match = True
            for condition in transition.conditions:
                try:
                    # Execute the lambda callable, unpacking the dynamic dictionary
                    if not condition(**locals):
                        match = False
                        break
                except AttributeError as e:
                    logger.debug(f"ISL Lambda Evaluation Short-Circuit: {e}")
                    match = False
                    break
                    
            if match:
                return transition.next
        
        return None


class LambdaTranslator(Translator):
    def __init__(self):
        self.env_globals = {
            "constants": SimpleNamespace(**Environ.constants),
            "functions": SimpleNamespace(**Environ.functions)
        }

    def compile(self, raw_configs: Dict[str, List[Any]]) -> Executor:
        compiled_transitions: Dict[str, List[Transition]] = {}

        for state_str, configs in raw_configs.items():
            compiled_transitions[state_str] = []
            
            for config in configs:
                callables: List[Callable] = []
                for cond_str in config.conditions:
                    try:
                        # Dynamic parameter list accommodates any dict passed via **locals
                        func_str = f"lambda sprite=None, sprites=None, plot=None, **kwargs: {cond_str}"
                        compiled_func = eval(func_str, self.env_globals)
                        callables.append(compiled_func)
                    except Exception as e:
                        logger.error(f"Failed to compile ISL lambda condition '{cond_str}': {e}")
                        
                compiled_transitions[state_str].append(
                    Transition(
                        next=config.next,
                        conditions=callables
                    )
                )
                
        return LambdaExecutor(transitions=compiled_transitions)