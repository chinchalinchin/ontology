"""
# Ontology: app.services.migrator

Package for state hydration and ECS component injection.
"""
import time
import dataclasses
import logging
from typing import Optional

from app.assets.base import Asset
from app.config.loader import Loader
from app.config.enums import AssetCategories, AssetInstances, Shortcuts
from app.services.factory import Factory
from app.services.generators.decomposer import Decomposer

logger = logging.getLogger(__name__)

class Migrator:
    """
    Time-sliced state machine for unpacking board state dynamically,
    preventing Python GIL locking during heavy loading operations.
    """
    def __init__(self, board, properties, configurations):
        self.board = board
        self.properties = properties
        self.configurations = configurations
        self.target: Optional[str] = None
        self.state = None
        self.decomposer = None
        self._generator = None
        
        # Track counts to bind to Loading Menu Meters
        self.maximum = 1
        self.current = 0

    def _build_generator(self):
        logger.info(f"Migrator starting hydration for target state: {self.target}")
        self.state = Loader.load_state(self.target)
        
        self.decomposer = Decomposer(
            compositions=self.configurations.compositions,
            properties=self.properties,
            recipes=self.configurations.recipes
        )
        
        # 1. Compile the manifest of objects to generate
        tasks = []
        if hasattr(self.state, Shortcuts.COMPOSITIONS.value) and self.state.compositions:
            for comp_state in self.state.compositions:
                tasks.append(('composition', comp_state))
                
        for cat_field in dataclasses.fields(self.state):
            category_key = cat_field.name
            if category_key == Shortcuts.COMPOSITIONS.value: 
                continue 
                
            category_data = getattr(self.state, category_key)
            if not category_data: 
                continue
            
            for inst_field in dataclasses.fields(category_data):
                instance_key = inst_field.name
                instance_list = getattr(category_data, instance_key)
                if not instance_list: 
                    continue
                
                for state_obj in instance_list:
                    tasks.append(('asset', category_key, instance_key, state_obj))
                    
        self.maximum = max(1, len(tasks))
        self.current = 0
        
        # 2. Yield through component injection
        for task in tasks:
            if task[0] == 'composition':
                comp_state = task[1]
                expanded_assets = self.decomposer.unpack(comp_state)
                self.board.add(expanded_assets)
            else:
                _, category_key, instance_key, state_obj = task
                asset_id = state_obj.id
                asset_name = getattr(state_obj, 'name', None) or asset_id
                
                cat_recipes = getattr(self.configurations.recipes, category_key, None)
                recipe = getattr(cat_recipes, instance_key, None) if cat_recipes else None
                
                prop_instance_key = instance_key
                if category_key == AssetCategories.SHEETS.value and \
                        instance_key == AssetInstances.PLAYERS.value:
                    prop_instance_key = AssetInstances.SPRITES.value
                    
                cat_props = getattr(self.properties, category_key, None)
                inst_props = getattr(cat_props, prop_instance_key, {}) if cat_props else {}
                props = inst_props.get(asset_id)
                
                asset = Asset(
                    taxonomy   = Factory.taxonomy(
                        asset_id, 
                        asset_name, 
                        category_key, 
                        instance_key
                    ),
                    properties = props,
                    state      = state_obj,
                    frame      = Factory.frame(recipe.frame) \
                                    if recipe and getattr(recipe, 'frame', None) \
                                        else Factory.frame(None),
                    animation  = Factory.animation(recipe.animation) \
                                    if recipe and getattr(recipe, 'animation', None) \
                                        else Factory.animation(None)
                )
                self.board.add([asset])
            
            self.current += 1
            yield True

    def step(self, budget_ms: int = 16) -> bool:
        """
        Executes generation tasks until the time budget is exhausted.
        Returns True when fully migrated, False if still working.
        """
        if not self.target:
            return True
            
        if self._generator is None:
            self._generator = self._build_generator()
            
        start = time.perf_counter()
        
        while True:
            # Yield execution back to Engine if time boundary is breached
            if (time.perf_counter() - start) * 1000 > budget_ms:
                return False
                
            try:
                next(self._generator)
            except StopIteration:
                self._generator = None
                self.target = None
                return True