import onta.settings as settings
import onta.engine.calculator as calculator
import onta.util.logger as logger

log = logger.Logger('onta.engine.collisions', settings.LOG_LEVEL)

def detect_hero_collision(hero_dim, hitbox_set):
    for hitbox_conf in hitbox_set.values():
        sets = hitbox_conf['sets']
        
        for hitbox in sets:
            strut_hitbox = hitbox.get('hitbox')
            if strut_hitbox is not None and calculator.intersection(hero_dim, strut_hitbox):
                # return true once collision is detected. it doesn't matter where it occurs, only what direction the hero is travelling...
                log.debug(f'Detected player {hero_dim} collision with hitbox at {strut_hitbox}', 'detect_hero_collisions')
                return True
