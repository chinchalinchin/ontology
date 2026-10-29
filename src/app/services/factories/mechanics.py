"""
@domain.system
@app.services
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
from app.models.config import MechanicsInstance
from app.services.translators import (
    CompilerTranslator,
    LambdaTranslator
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
        Devices.KEYBOARD.value: Keyboard,
        Devices.CONTROLLER.value: Controller,
    }

    MECHANICS_MAP = {
        Mechanics.ANIMATION.value: AnimationMechanics,
        Mechanics.COGNITION.value: CognitionMechanics,
        Mechanics.COLLISION.value: CollisionMechanics,
        Mechanics.COMBAT.value: CombatMechanics,
        Mechanics.FLUID.value: FluidMechanics,
        Mechanics.INTERACTION.value: InteractionMechanics,
        Mechanics.MENU.value: MenuMechanics,
        Mechanics.MOTION.value: MotionMechanics,
        Mechanics.NAVIGATION.value: NavigationMechanics,
        Mechanics.PLAYER.value: PlayerMechanics,
        Mechanics.PLOT.value: PlotMechanics,
        Mechanics.PROJECTILE.value: ProjectileMechanics,
        Mechanics.REMOVE.value: RemoveMechanics,
        Mechanics.SEASON.value: SeasonMechanics,
        Mechanics.SOCIAL.value: SocialMechanics,
        Mechanics.SWITCH.value: SwitchMechanics,
        Mechanics.TELEMETRY.value: TelemetryMechanics,
        Mechanics.TRANSITION.value: TransitionMechanics,
    }

    TRANSLATOR_MAP = {
        Translators.LAMBDA.value: LambdaTranslator,
        Translators.COMPILER.value: CompilerTranslator,
    }

    @classmethod
    def device(cls, dev: str, mapping: dict) -> Device:
        target_cls = cls.DEVICE_MAP.get(dev, Keyboard)
        return target_cls(mapping)

    @classmethod
    def translator(cls, translation: str):
        target_cls = cls.TRANSLATOR_MAP.get(translation, LambdaTranslator)
        return target_cls()

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