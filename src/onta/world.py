
import onta.settings as settings
import onta.load.state as state
import onta.util.logger as logger
import onta.graphics.calculator as calculator


log = logger.Logger('ontology.onta.world', settings.LOG_LEVEL)

class World():

    tilesets = None
    strutsets = None
    dimensions = None
    hero = None

    def __init__(self):
        self._init_static_layer()
        self._init_dynamic_layer()

    def _init_static_layer(self):
        static_conf = state.get_state('static')
        self.dimensions = (static_conf['dim']['w']*settings.TILE_DIM[0], 
            static_conf['dim']['h']*settings.TILE_DIM[1])
        self.tilesets = static_conf['tiles']
        self.strutsets = static_conf['struts']

        log.debug(f'Initialized static world layer with dimensions {self.dimensions}', 'world.World._init_static_layer')

    def _init_dynamic_layer(self):
        dynamic_conf = state.get_state('dynamic')
        self.hero = dynamic_conf['hero']

    def save(self):
        dynamic_conf = self.hero.copy()
        # dynamic_conf.update(self.other_conf)
        state.save_state('dynamic', dynamic_conf)

    def iterate(self, user_input: dict) -> dict:
        self._update_hero(user_input)
        pass

    def _update_hero(self, user_input:dict): 
        speed = self.hero['properties']['speed']

        if user_input['n']:
            self.hero['position']['y'] -= speed

        elif user_input['nw']:
            proj = calculator.projection()
            self.hero['position']['x'] -= speed*proj[0]
            self.hero['position']['y'] -= speed*proj[1]

        elif user_input['w']:
            self.hero['position']['x'] -= speed

        elif user_input['sw']:
            proj = calculator.projection()
            self.hero['position']['x'] -= speed*proj[0]
            self.hero['position']['y'] += speed*proj[1]

        elif user_input['s']:
            self.hero['position']['y'] += speed

        elif user_input['se']:
            proj = calculator.projection()
            self.hero['position']['x'] += speed*proj[0]
            self.hero['position']['y'] += speed*proj[1]

        elif user_input['e']:
            self.hero['position']['x'] += speed

        elif user_input['ne']:
            proj = calculator.projection()
            self.hero['position']['x'] += speed*proj[0]
            self.hero['position']['y'] -= speed*proj[1]

        pass