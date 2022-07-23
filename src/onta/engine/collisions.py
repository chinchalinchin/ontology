import onta.settings as settings
import onta.engine.calculator as calculator
import onta.util.logger as logger

log = logger.Logger('onta.engine.collisions', settings.LOG_LEVEL)

def detect_collision(sprite_dim, hitbox_list):
    for hitbox in hitbox_list:
        if hitbox is not None and calculator.intersection(sprite_dim, hitbox):
            # return true once collision is detected. it doesn't matter where it occurs, only what direction the hero is travelling...
            log.debug(f'Detected sprite {sprite_dim} collision with hitbox at {hitbox}', 
                'detect_hero_collisions')
            return True

def recoil_sprite(sprite_state, sprite_props):
    # TODO: pass in collide directly instead of through dictionary
    if 'down' in sprite_state['state']:
        sprite_state['position']['y'] -= sprite_props['collide']
    elif 'left' in sprite_state['state']:
        sprite_state['position']['x'] -= sprite_props['collide']
    elif 'right' in sprite_state['state']:
        sprite_state['position']['x'] += sprite_props['collide']
    else:
        sprite_state['position']['y'] += sprite_props['collide']