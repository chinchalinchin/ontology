"""
# Ontology: app.game.logic.mechanics.motion.motive
"""
# Standard Libraries
from typing import List, TYPE_CHECKING

# Application Libraries
from app.assets.base import Asset
from app.config.enums import NavigationIntentions

if TYPE_CHECKING:
    from app.game.board import Board

# Cython Libraries
import libs.core.math.physics as physics
import libs.core.math.geometry as geometry


def update(sprites: List[Asset], board: Board, delta: float) -> None:
    """
    Evaluates pathfinding trajectories and steers autonomous sprites using
    Reciprocal Velocity Obstacles (RVO) around neighboring entities.
    """
    player_name = board.player().name

    for sprite in sprites:
        if not sprite.state.goal or sprite.state.intention not in NavigationIntentions:
            sprite.state.velocity.vx = 0.0
            sprite.state.velocity.vy = 0.0
            continue

        target_pos = sprite.state.trajectory.target or sprite.state.goal.position
        if not target_pos:
            sprite.state.velocity.vx = 0.0
            sprite.state.velocity.vy = 0.0
            continue

        pref_vel = physics.aim(
            sprite.state.position,
            target_pos,
            sprite.state.character.speed
        )

        squeeze_radius = sprite.state.mutators.parameters.squeeze.radius
        half_w = sprite.dimensions.w / 2.0

        neighbors = [
            (
                char.position.x + half_w,
                char.position.y + half_w,
                char.velocity.vx,
                char.velocity.vy,
                half_w,
                name == player_name
            )
            for name, char in board.characters().items()
            if name != sprite.name
            and char.layer == sprite.state.layer
            and geometry.nearby(
                char.position.x, 
                char.position.y, 
                sprite.state.position.x, 
                sprite.state.position.y, 
                squeeze_radius
            )
        ]

        avoid_vel = physics.avoid(
            sprite.primitive(),
            pref_vel,
            neighbors,
            delta
        )

        ## KINEMATIC SLIDING
        # NOTE: more performant. keep.
        sprite.state.velocity.vx = avoid_vel.vx
        sprite.state.velocity.vy = avoid_vel.vy

        ## DYNAMIC STEERING
        # physics.dynamics(
        #     sprite.state.velocity,
        #     sprite.state.position.x,
        #     sprite.state.position.y,
        #     sprite.state.position.x + avoid_vel.vx,
        #     sprite.state.position.y + avoid_vel.vy,
        #     sprite.state.character.speed,
        #     sprite.state.character.impulse,
        #     delta
        # )