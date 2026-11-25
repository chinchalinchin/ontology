"""
@domain.system
@app.service
@app.mechanic
@workflow.injection

# Ontology: Source - app.services.factories.mechanics

Factory for instantiating Mechanics, Translators, and Input Devices.
"""
from __future__ import annotations

# Standard Libraries
from typing import (
    Any,
    Dict,
    Optional
)

# Application Libraries
from app.game.devices import (
    Controller,
    Device,
    Keyboard
)
from app.game.logic.mechanics import (
    AnimationMechanics,
    CognitionMechanics,
    CollisionMechanics,
    CombatMechanics,
    FluidMechanics,
    InteractionMechanics,
    Mechanic,
    MenuMechanics,
    MotionMechanics,
    NavigationMechanics,
    PlayerMechanics,
    PlotMechanics,
    ProjectileMechanics,
    RemoveMechanics,
    SeasonMechanics,
    SocialMechanics,
    SwitchMechanics,
    TelemetryMechanics,
    TransitionMechanics
)
from app.models.configurations import MechanicsInstance
from app.services.translators import (
    ConditionBackend,
    CompilerConditionBackend,
    LambdaConditionBackend,
    CompilerTranslator,
    LambdaTranslator,
    GoalTranslator,
    Translator,
)
from app.static.semantics import (
    Devices,
    Mechanics,
    Translators
)


class MechanicFactory:
    """
    Factory for constructing engine pipeline Mechanics, Translators, and Devices.
    """
    DEVICE_MAP = {
        Devices.KEYBOARD: Keyboard,
        Devices.CONTROLLER: Controller,
    }

    MECHANICS_MAP = {
        Mechanics.ANIMATION: AnimationMechanics,
        Mechanics.COGNITION: CognitionMechanics,
        Mechanics.COLLISION: CollisionMechanics,
        Mechanics.COMBAT: CombatMechanics,
        Mechanics.FLUID: FluidMechanics,
        Mechanics.INTERACTION: InteractionMechanics,
        Mechanics.MENU: MenuMechanics,
        Mechanics.MOTION: MotionMechanics,
        Mechanics.NAVIGATION: NavigationMechanics,
        Mechanics.PLAYER: PlayerMechanics,
        Mechanics.PLOT: PlotMechanics,
        Mechanics.PROJECTILE: ProjectileMechanics,
        Mechanics.REMOVE: RemoveMechanics,
        Mechanics.SEASON: SeasonMechanics,
        Mechanics.SOCIAL: SocialMechanics,
        Mechanics.SWITCH: SwitchMechanics,
        Mechanics.TELEMETRY: TelemetryMechanics,
        Mechanics.TRANSITION: TransitionMechanics,
    }

    TRANSLATOR_MAP = {
        Translators.LAMBDA: LambdaTranslator,
        Translators.COMPILER: CompilerTranslator,
    }

    @classmethod
    def device(cls, dev: str, mapping: dict) -> Device:
        target_cls = cls.DEVICE_MAP.get(dev, Keyboard)
        return target_cls(mapping)

    @staticmethod
    def backend(implementation: str) -> ConditionBackend:
        if implementation == Translators.COMPILER:
            return CompilerConditionBackend()
        if implementation == Translators.LAMBDA:
            return LambdaConditionBackend()
        raise ValueError(f"Unsupported translator implementation: '{implementation}'")

    @staticmethod
    def translator(implementation: str) -> Translator:
        backend = MechanicFactory.condition_backend(implementation)
        if isinstance(backend, CompilerConditionBackend):
            return CompilerTranslator(backend=backend)
        return LambdaTranslator(backend=backend)

    @staticmethod
    def goals(implementation: str) -> GoalTranslator:
        return GoalTranslator(
            backend=MechanicFactory.condition_backend(implementation)
        )
    
    @classmethod
    def mechanics(
        cls,
        config: MechanicsInstance,
        executors: Optional[Dict[str, Any]] = None,
        relations: Optional[Dict[str, Any]] = None
    ) -> Mechanic:
        key = config.key
        target_cls = cls.MECHANICS_MAP.get(key, AnimationMechanics)
        mechanic_instance = target_cls()

        # 1. Resolve and inject executors
        executor_keys = config.executors
        if executor_keys:
            if executors is None:
                raise KeyError(
                    f"Mechanic '{key}' declared executors {executor_keys}, "
                    f"but no executor registry was provided."
                )
            for executor_key in executor_keys:
                executor = executors.get(executor_key)
                if executor is None:
                    raise KeyError(
                        f"Mechanic '{key}' requested executor '{executor_key}', "
                        f"but it is not registered in the active executor map."
                    )
                mechanic_instance.set_executor(executor_key, executor)

        # 2. Resolve and inject relations
        relation_keys = config.relations
        if relation_keys:
            if relations is None:
                raise KeyError(
                    f"Mechanic '{key}' declared relations {relation_keys}, "
                    f"but no relations registry was provided."
                )
            for relation_key in relation_keys:
                relation = relations.get(relation_key)
                if relation is None:
                    raise KeyError(
                        f"Mechanic '{key}' requested relation '{relation_key}', "
                        f"but it is not registered in the active relations map."
                    )
                mechanic_instance.set_relation(relation_key, relation)

        return mechanic_instance