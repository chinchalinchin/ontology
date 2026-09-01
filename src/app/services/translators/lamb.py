"""
# Ontology: app.services.translators.lamb
"""
import logging
from typing import Dict, List, Optional, Any, Callable

from app.config.settings import ISL_ENVIRONMENT
from app.config.enums import Intentions
from app.models.state import SpriteState
from app.models.config import IntentionConfiguration
from app.services.translators.base import Translator, Executor, IntentionTransition

logger = logging.getLogger(__name__)

class LambdaExecutor(Executor):
    def evaluate(self, sprite: SpriteState, sprites: Dict[str, Any]) -> Optional[Intentions]:
        if sprite.intention not in self.transitions:
            return None
            
        for transition in self.transitions[sprite.intention]:
            if not transition.conditions:
                continue
                
            match = True
            for condition in transition.conditions:
                try:
                    # Execute the lambda callable
                    if not condition(sprite, sprites):
                        match = False
                        break
                except AttributeError as e:
                    logger.debug(f"ISL Lambda Evaluation Short-Circuit: {e}")
                    match = False
                    break
                    
            if match:
                return transition.next_intention
        
        return None


class LambdaTranslator(Translator):
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
                    
                callables: List[Callable] = []
                for cond_str in config.conditions:
                    try:
                        func_str = f"lambda sprite, sprites: {cond_str}"
                        compiled_func = eval(func_str, ISL_ENVIRONMENT)
                        callables.append(compiled_func)
                    except Exception as e:
                        logger.error(f"Failed to compile ISL lambda condition '{cond_str}': {e}")
                        
                compiled_transitions[intention_key].append(
                    IntentionTransition(
                        next_intention=next_intention,
                        conditions=callables
                    )
                )
                
        return LambdaExecutor(transitions=compiled_transitions)