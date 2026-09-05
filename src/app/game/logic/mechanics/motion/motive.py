"""
# Ontology: app.game.logic.mechanics.motion.motive
"""
# Standard Libraries
import math

# Application Libraries
from app.config.enums import NavigationIntentions

def update(sprites, delta):
    """
    Evaluates pathfinding and translates distance to target into vector velocities with friction emulation.
    """
    for sprite in sprites:
        if not sprite.state.goal or sprite.state.intention not in NavigationIntentions:
            sprite.state.velocity.vx = 0.0
            sprite.state.velocity.vy = 0.0
            continue

        dx = sprite.state.goal.position.x - sprite.state.position.x
        dy = sprite.state.goal.position.y - sprite.state.position.y

        if dx == 0 and dy == 0:
            sprite.state.velocity.vx = 0.0
            sprite.state.velocity.vy = 0.0
            continue

        mag = math.sqrt(dx*dx + dy*dy)
        speed = sprite.state.character.speed
        
        # Clamp velocity if within arrival threshold to prevent oscillation 
        if mag < speed * delta:
            sprite.state.velocity.vx = dx / delta
            sprite.state.velocity.vy = dy / delta

        else:
            ux, uy = dx / mag, dy / mag
            impulse = sprite.state.character.impulse

            sprite.state.velocity.vx += ux * impulse * delta
            sprite.state.velocity.vy += uy * impulse * delta

            vmag = math.sqrt(sprite.state.velocity.vx**2 + sprite.state.velocity.vy**2)
            if vmag > speed:
                sprite.state.velocity.vx = (sprite.state.velocity.vx / vmag) * speed
                sprite.state.velocity.vy = (sprite.state.velocity.vy / vmag) * speed