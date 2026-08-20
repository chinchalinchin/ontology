"""
# Ontology: app.game.logic.mechanics.motion.frictive
"""
# Standard Libraries
import math

# Cython Libraries
from libs.core.models import Position

def update(crates, board, delta):
    """
    Determines linear velocity decay based on environmental properties for inert moving assets.
    """
    for crate in crates:
        if not hasattr(crate.state, 'velocity') or crate.state.velocity is None:
            continue

        w = crate.dimensions.w if crate.dimensions else 0
        l = crate.dimensions.l if crate.dimensions else 0
        cx = crate.state.position.x + (w / 2.0)
        cy = crate.state.position.y + (l / 2.0)
        
        center_pos = Position(int(cx), int(cy))
        tile = board.tile(crate.state.layer, center_pos)

        if tile and hasattr(tile.properties, 'friction'):
            friction = tile.properties.friction
            dv = friction * delta

            vx = crate.state.velocity.vx
            vy = crate.state.velocity.vy
            vmag = math.sqrt(vx*vx + vy*vy)

            if vmag > 0:
                if dv >= vmag:
                    crate.state.velocity.vx = 0.0
                    crate.state.velocity.vy = 0.0
                else:
                    ux, uy = vx / vmag, vy / vmag
                    crate.state.velocity.vx -= ux * dv
                    crate.state.velocity.vy -= uy * dv