"""
# Ontology: app.services.translators.compiler
"""
import logging
from types import SimpleNamespace
from typing import Dict, List, Optional, Any

from app.services.translators.base import (
    Translator, 
    Executor, 
    Transition
)
from app.services.translators.environ import Environ

logger = logging.getLogger(__name__)

class CompilerExecutor(Executor):
    def __init__(self, transitions: Dict[str, List[Transition]]):
        super().__init__(transitions)
        # Construct the globals dictionary once
        self.env_globals = {
            "constants": SimpleNamespace(**Environ.constants),
            "functions": SimpleNamespace(**Environ.functions)
        }

    def evaluate(self, current_state: str, locals: Dict[str, Any]) -> Optional[str]:
        if current_state not in self.transitions:
            return None
            
        for transition in self.transitions[current_state]:
            if not transition.conditions:
                continue
                
            match = True
            for code_obj in transition.conditions:
                try:
                    # Evaluate the compiled AST object using the cached globals and dynamic locals
                    if not eval(code_obj, self.env_globals, locals):
                        match = False
                        break
                except AttributeError as e:
                    logger.debug(f"ISL AST Evaluation Short-Circuit: {e}")
                    match = False
                    break
                    
            if match:
                return transition.next
                
        return None


class CompilerTranslator(Translator):
    def compile(self, raw_configs: Dict[str, List[Any]]) -> Executor:
        compiled_transitions: Dict[str, List[Transition]] = {}
        
        for state_str, configs in raw_configs.items():
            compiled_transitions[state_str] = []
            
            for config in configs:
                code_objects: List[Any] = []
                for cond_str in config.conditions:
                    try:
                        code_obj = compile(cond_str, '<string>', 'eval')
                        code_objects.append(code_obj)
                    except Exception as e:
                        logger.error(f"Failed to compile ISL AST condition '{cond_str}': {e}")
                        
                compiled_transitions[state_str].append(
                    Transition(
                        next=config.next,
                        conditions=code_objects
                    )
                )
                
        return CompilerExecutor(transitions=compiled_transitions)