"""
# Ontology: app.game.logic.mechanics.motion.kinematic
"""
# Standard Libraries
import math

# Application Libraries
from app.config.enums import PlayerGoals

def update(players, mapping, delta):
    """
    Snaps axis and applies velocity to kinematic player entities without generating impulses.
    """
    for player in players:
        ix, iy = 0.0, 0.0
        if PlayerGoals.UP in mapping.goals: iy -= 1.0
        if PlayerGoals.DOWN in mapping.goals: iy += 1.0
        if PlayerGoals.LEFT in mapping.goals: ix -= 1.0
        if PlayerGoals.RIGHT in mapping.goals: ix += 1.0

        # Axis-Snapping logic: nullify orthogonal axes for cardinal movement precedence
        if ix != 0.0 and iy == 0.0:
            player.state.velocity.vy = 0.0
        if iy != 0.0 and ix == 0.0:
            player.state.velocity.vx = 0.0

        if ix != 0.0 or iy != 0.0:
            # Retain diagonal support and normalize
            mag = math.sqrt(ix*ix + iy*iy)
            ux, uy = ix / mag, iy / mag
            
            speed = player.state.character.speed
            # Bypass impulse. Set max magnitude immediately.
            player.state.velocity.vx = ux * speed
            player.state.velocity.vy = uy * speed
        else:
            player.state.velocity.vx = 0.0
            player.state.velocity.vy = 0.0