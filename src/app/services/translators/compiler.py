"""
# Ontology: app.services.translators.compiler
"""
import logging
from typing import Dict, List, Optional, Any

from app.config.settings import ISL_ENVIRONMENT
from app.config.enums import Intentions
from app.models.state import SpriteState
from app.models.config import IntentionConfiguration
from app.services.translators.base import Translator, Executor, IntentionTransition

logger = logging.getLogger(__name__)

class CompilerExecutor(Executor):
    def evaluate(self, sprite: SpriteState, sprites: Dict[str, Any]) -> Optional[Intentions]:
        if sprite.intention not in self.transitions:
            return None
            
        # Bind the dynamic execution locals
        execution_locals = {
            'sprite': sprite,
            'sprites': sprites
        }
            
        for transition in self.transitions[sprite.intention]:
            if not transition.conditions:
                continue
                
            match = True
            for code_obj in transition.conditions:
                try:
                    # Evaluate the compiled AST object
                    if not eval(code_obj, ISL_ENVIRONMENT, execution_locals):
                        match = False
                        break
                except AttributeError as e:
                    logger.debug(f"ISL AST Evaluation Short-Circuit: {e}")
                    match = False
                    break
                    
            if match:
                return transition.next_intention
                
        return None


class CompilerTranslator(Translator):
    def compile(self, raw_intentions: Dict[str, List[IntentionConfiguration]]) -> Executor:
        compiled_transitions: Dict[Intentions, List[IntentionTransition]] = {}
        
        for state_str, configs in raw_intentions.items():
            try:
                intention_key = Intentions(state_str)
            except ValueError:
                logger.warning(f"Unrecognized Intention key in ISL configuration: {state_str}")
                continue
                
            compiled_transitions[intention_key] = []
            
            for config in configs:
                try:
                    next_intention = Intentions(config.next)
                except ValueError:
                    logger.warning(f"Unrecognized Target Intention in ISL configuration: {config.next}")
                    continue
                    
                code_objects: List[Any] = []
                for cond_str in config.conditions:
                    try:
                        code_obj = compile(cond_str, '<string>', 'eval')
                        code_objects.append(code_obj)
                    except Exception as e:
                        logger.error(f"Failed to compile ISL AST condition '{cond_str}': {e}")
                        
                compiled_transitions[intention_key].append(
                    IntentionTransition(
                        next=next_intention,
                        conditions=code_objects
                    )
                )
                
        return CompilerExecutor(transitions=compiled_transitions)