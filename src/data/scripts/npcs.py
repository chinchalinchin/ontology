import onta.world as world
import onta.settings as settings
import onta.util.logger as logger

log = logger.Logger('data.scripts', settings.LOG_LEVEL)

def state_handler(game_world: world.World):
    log.debug('Script was injected!', 'state_handler')
    pass