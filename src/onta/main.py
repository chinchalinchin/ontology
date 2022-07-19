import sys
import threading

import onta.view as view
import onta.control as control
import onta.world as world
import onta.settings as settings
import onta.util.logger as logger

log = logger.Logger('ontology.onta.main', settings.LOG_LEVEL)

def be():
    app, game = view.init(), view.view()
    game_loop = threading.Thread(target=do, daemon=True)
    game_loop.start()
    game.show()
    view.quit(app)
    
def do():
    while True:
        user_input = control.poll()
        log.debug(f'User Input: {user_input}', 'loop')

        world_state = world.iterate(user_input)
        log.debug(f'World State: {world_state}', 'loop')

        view.render(world_state)

if __name__=="__main__":
    be()