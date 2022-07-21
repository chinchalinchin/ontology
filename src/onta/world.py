
import onta.settings as settings
import onta.load.state as state
import onta.load.conf as conf
import onta.util.logger as logger
import onta.engine.calculator as calculator
import onta.engine.collisions as collisions

log = logger.Logger('ontology.onta.world', settings.LOG_LEVEL)

CONFIGURABLE_ELEMENTS = [ 'struts', 'sprites' ]

class World():

    strut_property_conf = None
    """
    Holds strut property configuration information
    ```python
    self.strut_property_conf = {
            'strut_1': {
                'hitbox_1': hitbox_1_dim, # tuple
                'hitbox_2': hitbox_2_dim, # tuple
                # ...
            }
        }
    ```
    """
    sprite_state_conf = None
    """
    Holds sprite state configuration information.

    ```python
    self.sprite_state_conf = {
        'sprite_1': {
            'state_1': state_1_frames, # int
            'state_2': state_2_frames, # int
            # ..
            'blocking_states': [ block_state_1, block_state_2, ], # list(str)
        }

    }
    ```
    """
    sprite_property_conf = None
    tilesets = None
    """
    ```python
    self.tilesets = {
        'tile_1': {
            'sets': [
                { 
                    'start': {
                        'tile_units': tile_units, # bool
                        'x': x, # int
                        'y': y, # int
                    }
                }
            ]
        }
    }
    ```
    """
    strutsets = None
    """
    ```python
    self.strutsets = {
        'strut_1': {
            'sets': [
                { 
                    'start': {
                        'tile_units': tile_units, # bool
                        'x': x, # int
                        'y': y, # int
                    },
                    'hitbox': (hx, hy, hw, hh), # tuple(int, int, int, int)

                }
            ]
        }
    }
    ```
    """
    dimensions = None
    hero = None

    def __init__(self):
        self._init_conf()
        self._init_static_state()
        self._init_dynamic_state()
        self._init_hitboxes()

    def _init_conf(self):
        """
        
        Initialize configuration properties for in-game elements in the memory.
        """
        struts_conf = conf.configuration('struts')
        sprites_conf = conf.configuration('sprites')

        self.sprite_state_conf = {}
        self.sprite_property_conf = {}
        for sprite_key, sprite_conf in sprites_conf.items():
            # transfer fields that don't require condensing
            self.sprite_state_conf[sprite_key] = {}
            self.sprite_property_conf[sprite_key] = {}

            self.sprite_property_conf[sprite_key]['hitbox'] = (
                sprite_conf['properties']['hitbox']['offset']['x'],
                sprite_conf['properties']['hitbox']['offset']['y'],
                sprite_conf['properties']['hitbox']['size']['w'],
                sprite_conf['properties']['hitbox']['size']['h']
            )
            self.sprite_property_conf[sprite_key]['walk'] = sprite_conf['properties']['walk']
            self.sprite_property_conf[sprite_key]['run'] = sprite_conf['properties']['run']
            self.sprite_property_conf[sprite_key]['collide'] = sprite_conf['properties']['collide']

            self.sprite_state_conf[sprite_key]['size'] = {}
            self.sprite_state_conf[sprite_key]['size']['w'] = sprite_conf['size']['w']
            self.sprite_state_conf[sprite_key]['size']['h'] = sprite_conf['size']['h']
            self.sprite_state_conf[sprite_key]['blocking_states'] = sprite_conf['blocking_states']

            # condense state information to only info relevant to World 
            #   i.e., the World doesn't care about the state image configuration
            for state_map in sprite_conf['states']:
                state = list(state_map.keys())[0]
                self.sprite_state_conf[sprite_key][state] = state_map[state]['frames']

        self.strut_property_conf = {}
        
        for strut_key, strut_conf in struts_conf.items():
            self.strut_property_conf[strut_key] = {}
            hitbox = strut_conf['properties']['hitbox']

            self.strut_property_conf[strut_key]['size'] = {}
            self.strut_property_conf[strut_key]['size']['w'] = strut_conf['image']['size']['w']
            self.strut_property_conf[strut_key]['size']['h'] = strut_conf['image']['size']['h']

            if hitbox is not None:
                self.strut_property_conf[strut_key]['hitbox'] = (hitbox['offset']['x'], hitbox['offset']['y'],
                    hitbox['size']['w'], hitbox['size']['h'])
            else:
                self.strut_property_conf[strut_key]['hitbox'] = None

    def _init_static_state(self):
        """
        Initialize the state for static in-game elements, i.e. elements that do not move and are not interactable.
        """
        static_conf = state.get_state('static')
        self.dimensions = (static_conf['dim']['w']*settings.TILE_DIM[0], 
            static_conf['dim']['h']*settings.TILE_DIM[1])
        self.tilesets = static_conf['tiles']
        self.strutsets = static_conf['struts']

        log.debug(f'Initialized static world layer with dimensions {self.dimensions}', 'World._init_static_layer')

    def _init_dynamic_state(self):
        """
        Initialize the state for dynamic in-game elements, i.e.e elements that move and are interactable.
        """
        dynamic_conf = state.get_state('dynamic')
        self.hero = dynamic_conf['hero']

    def _init_hitboxes(self):
        buffer_strutsets = self.strutsets.copy()

        for strutset_key, strutset_conf in buffer_strutsets.items():
            strutset_props = self.strut_property_conf[strutset_key]
            strutset_hitbox = strutset_props['hitbox']
            strutset = strutset_conf['sets']

            log.debug(f'Initialize strutset {strutset_key} with properties: {strutset_props}', 'World._init_hitboxes')

            for i, strut_conf in enumerate(strutset):

                if strutset_hitbox is not None:
                    if strut_conf['start']['tile_units'] == 'default':
                        x = strut_conf['start']['x']*settings.TILE_DIM[0]
                        y = strut_conf['start']['y']*settings.TILE_DIM[1]
                    if strut_conf['start']['tile_units'] == 'relative':
                        x = strut_conf['start']['x']*strutset_props['size']['w']
                        y = strut_conf['start']['y']*strutset_props['size']['h']
                    else:
                        x, y = strut_conf['start']['x'], strut_conf['start']['y']
                    
                    top_x, top_y = x + strutset_hitbox[0], y + strutset_hitbox[1]
                    
                    self.strutsets[strutset_key]['sets'][i]['hitbox'] = (top_x, top_y,
                        strutset_hitbox[2], strutset_hitbox[3])
                else:
                    self.strutsets[strutset_key]['sets'][i]['hitbox'] = None

    def _update_hero(self, user_input:dict): 
        """
        Map user input to new hero state and then animate state.
        """

        if 'run' in self.hero['state']:
            speed = self.sprite_property_conf['hero']['run']
        else:
            speed = self.sprite_property_conf['hero']['walk']

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

    def _apply_physics(self):
        static_hero_props = self.sprite_property_conf['hero']
        hero_hitbox = (
            self.hero['position']['x'] + static_hero_props['hitbox'][0], 
            self.hero['position']['y'] + static_hero_props['hitbox'][1],
            static_hero_props['hitbox'][2],
            static_hero_props['hitbox'][3]
        )
        if collisions.detect_hero_collision(hero_hitbox, self.strutsets):
            if 'down' in self.hero['state']:
                self.hero['position']['y'] -= static_hero_props['collide']
            elif 'left' in self.hero['state']:
                self.hero['position']['x'] -= static_hero_props['collide']
            elif 'right' in self.hero['state']:
                self.hero['position']['x'] += static_hero_props['collide']
            else:
                self.hero['position']['y'] += static_hero_props['collide']
                

    def save(self):
        dynamic_conf = self.hero.copy()
        # dynamic_conf.update(self.other_conf)
        state.save_state('dynamic', dynamic_conf)

    def iterate(self, user_input: dict) -> dict:
        """
        Update the world state.
        """
        self._update_hero(user_input)
        self._apply_physics()