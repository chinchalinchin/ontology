
import onta.settings as settings
import onta.load.state as state
import onta.load.conf as conf
import onta.util.logger as logger
import onta.graphics.calculator as calculator


log = logger.Logger('ontology.onta.world', settings.LOG_LEVEL)

CONFIGURABLE_ELEMENTS = [ 'struts', 'sprites' ]
class World():

    strut_state_conf = None
    sprite_state_conf = None
    tilesets = None
    strutsets = None
    dimensions = None
    hero = None

    def __init__(self):
        self._init_conf()
        self._init_static_state()
        self._init_dynamic_state()

    def _init_conf(self):
        """
        
        Initialize configuration properties for in-game elements.

        ```python
        self.sprite_state_conf = {
            'sprite_1': {
                'state_1': state_1_frames, # int
                'state_2': state_2_frames, # int
                # ..
                'blocking_states': [ block_state_1, block_state_2, ], # list(str)
            }

        }
        self.strut_property_conf
        ```
        """
        struts_conf = conf.configuration('struts')
        sprites_conf = conf.configuration('sprites')

        self.sprite_state_conf = {}

        for sprite_key, sprite_conf in sprites_conf.items():
            for state_map in sprite_conf['states']:
                state = list(state_map.keys())[0]
                self.sprite_state_conf[sprite_key] = {}
                self.sprite_state_conf[sprite_key][state] = state_map[state]['frames']
            self.sprite_state_conf[sprite_key]['blocking_states'] = state_map['blocking_states']

        self.strut_state_conf = {}
        
        for strut_key, strut_conf in struts_conf.items():
            hitbox = strut_conf['properties']['hitbox']

            self.strut_state_conf[strut_key] = {}
            self.strut_state_conf[strut_key]['hitbox'] = (hitbox['offset']['x'], hitbox['offset']['y'],
                hitbox['size']['w'], hitbox['size']['h'])

    def _init_static_state(self):
        """
        Initialize the state for static in-game elements, i.e. elements that do not move and are not interactable.
        """
        static_conf = state.get_state('static')
        self.dimensions = (static_conf['dim']['w']*settings.TILE_DIM[0], 
            static_conf['dim']['h']*settings.TILE_DIM[1])
        self.tilesets = static_conf['tiles']
        self.strutsets = static_conf['struts']

        log.debug(f'Initialized static world layer with dimensions {self.dimensions}', 'world.World._init_static_layer')

    def _init_dynamic_state(self):
        """
        Initialize the state for dynamic in-game elements, i.e.e elements that move and are interactable.
        """
        dynamic_conf = state.get_state('dynamic')
        self.hero = dynamic_conf['hero']

    def _update_hero(self, user_input:dict): 
        """
        Map user input to new hero state and then animate state.
        """
        static_hero_conf = self.sprite_state_conf['hero']
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

        if self.hero['frame'] >= static_hero_conf[self.hero['state']]:
            self.hero['frame'] = 0

    def _calculate_collisions(self):
        pass

    def save(self):
        dynamic_conf = self.hero.copy()
        # dynamic_conf.update(self.other_conf)
        state.save_state('dynamic', dynamic_conf)

    def iterate(self, user_input: dict) -> dict:
        """
        Update the world state.
        """
        self._update_hero(user_input)
        self._calculate_collisions()