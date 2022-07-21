
import onta.settings as settings
import onta.load.state as state
import onta.util.logger as logger
import onta.graphics.calculator as calculator


log = logger.Logger('ontology.onta.world', settings.LOG_LEVEL)

class World():

    sprite_state_conf = None
    tilesets = None
    strutsets = None
    dimensions = None
    hero = None

    def __init__(self, sprite_state_conf):
        self.sprite_state_conf = sprite_state_conf
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
            if self.hero['state'] != 'walk_up':
                self.hero['frame'] = 0
                self.hero['state'] = 'walk_up'

            else:
                self.hero['frame'] += 1

            self.hero['position']['y'] -= speed

        elif user_input['s']:
            if self.hero['state'] != 'walk_down':
                self.hero['frame'] = 0
                self.hero['state'] = 'walk_down'

            else:
                self.hero['frame'] += 1

            self.hero['position']['y'] += speed

        elif user_input['nw'] or user_input['w'] or user_input['sw']:
            if self.hero['state'] != 'walk_right':
                self.hero['frame'] = 0
                self.hero['state'] = 'walk_right'

            else:
                self.hero['frame'] += 1

            if user_input['nw'] or user_input['sw']:    
                proj = calculator.projection()

                if user_input['nw']:
                    self.hero['position']['x'] -= speed*proj[0]
                    self.hero['position']['y'] -= speed*proj[1]

                elif user_input['sw']:
                    self.hero['position']['x'] -= speed*proj[0]

                self.hero['position']['y'] += speed*proj[1]

            elif user_input['w']:
                self.hero['position']['x'] -= speed

        elif user_input['se'] or user_input['e'] or user_input['ne']:
            if self.hero['state'] != 'walk_left':
                self.hero['frame'] = 0
                self.hero['state'] = 'walk_left'
            else:
                self.hero['frame'] += 1

            if user_input['se'] or user_input['ne']:
                proj = calculator.projection()

                if user_input['se']:
                    self.hero['position']['x'] += speed*proj[0]
                    self.hero['position']['y'] += speed*proj[1]

                elif user_input['ne']:
                    self.hero['position']['x'] += speed*proj[0]
                    self.hero['position']['y'] -= speed*proj[1]

            elif user_input['e']:
                self.hero['position']['x'] += speed

        if self.hero['frame'] >= self.sprite_state_conf['hero'][self.hero['state']]:
            self.hero['frame'] = 0