
import onta.settings as settings
import onta.load.state as state
import onta.load.conf as conf
import onta.util.logger as logger
import onta.engine.calculator as calculator
import onta.engine.collisions as collisions

log = logger.Logger('onta.world', settings.LOG_LEVEL)

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
    """
    ```python
    self.sprite_property_conf = {
        'sprite_1': {
            'walk': walk, # int,
            'run': run, # int,
            'collide': collide, # int
            'hitbox': {
                'offset': {
                    'x': x, # int
                    'y': y, #int
                },
                'size': {
                    'w' : w, # int
                    'h' : h, # int
                }
            }
        }
    }
    ```
    """
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
    """
    ```
    self.dimensions = (w, h) # tuple
    ```
    """
    hero = None
    """
    ```python
    self.hero = {
        'position': {
            'x': x, # float,
            'y': y, # float
        },
        'state': state, # str,
        'frame': frame, # int
    }
    ```
    """
    npcs = None
    """
    ```python
    self.npcs = {
        'npc_1': {
            'position: {
                'x': x, # float
                'y': y, # float
            },
            'state': state, # string
            'frame': frame, # int
        },
    }
    ```
    """
    villains = None
    """
    ```python
    self.villains = {
        'vil_1': {
            'position: {
                'x': x, # float
                'y': y, # float
            },
            'state': state, # string
            'frame': frame, # int
        },
    }
    ```
    """

    def __init__(self, config: conf.Conf, state_ao: state.State):
        """
        Creates an instance of `onta.world.World`.

        .. notes:
            - Configuration and state are passed in to populate internal dictionaries. No references are kept to the `config` or `state_ao` objects.
        """
        self._init_conf(config)
        self._init_static_state(state_ao)
        self._init_dynamic_state(state_ao)
        self._init_static_hitboxes()

    def _init_conf(self, config: conf.Conf):
        """
        
        Initialize configuration properties for in-game elements in the memory.
        """
        struts_conf = config.configuration('struts')
        sprites_conf = config.configuration('sprites')

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

    def _init_static_state(self, state_ao: state.State):
        """
        Initialize the state for static in-game elements, i.e. elements that do not move and are not interactable.
        """
        static_conf = state_ao.get_state('static')
        self.dimensions = (static_conf['dim']['w']*settings.TILE_DIM[0], 
            static_conf['dim']['h']*settings.TILE_DIM[1])
        self.tilesets = static_conf['tiles']
        self.strutsets = static_conf['struts']

        log.debug(f'Initialized static world layer with dimensions {self.dimensions}', 'World._init_static_layer')

    def _init_dynamic_state(self, state_ao: state.State):
        """
        Initialize the state for dynamic in-game elements, i.e. elements that move and are interactable.
        """
        dynamic_conf = state_ao.get_state('dynamic')
        self.hero = dynamic_conf['hero']
        self.npcs = dynamic_conf['npcs']
        self.villains = dynamic_conf['villains']

    def _init_static_hitboxes(self):
        """
        Construct static hitboxes from object dimensions and properties.
        """
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
        
        # condense all the hitboxes into a list and save to strutsets,
        # to avoid repeated internal calls to `get_strut_hitboxes`
        self.strutsets['hitboxes'] = self.get_strut_hitboxes()

    def _update_hero(self, user_input: dict): 
        """
        Map user input to new hero state, apply state action and iterate state frame.
        """
        if self.hero['state'] not in self.sprite_state_conf['hero']['blocking_states']:
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

    def _update_npcs(self):
        """
        Maps npc state to in-game action, applies action and then iterates npc state frame.

        .. notes:
            - This method is essentially an interface between the NPC state and the game world. It determines what happens to an NPC once it is in a state.
        """
        for npc_key, npc_state in self.npcs.items():
            npc_props = self.sprite_property_conf[npc_key]

            # TODO: hit detection


    def _apply_physics(self):
        hero_props = self.sprite_property_conf['hero']
        hero_hitbox = self.get_hero_hitbox()
        npcs_hitboxes = self.get_sprite_hitboxes('npcs')    
        vil_hitboxes = self.get_sprite_hitboxes('villains')

        collision_sets = [npcs_hitboxes, vil_hitboxes, self.strutsets['hitboxes']]

        for collision_set in collision_sets:
            if collisions.detect_hero_collision(hero_hitbox, collision_set):
                collisions.recoil_sprite(self.hero, hero_props)
        
    def _apply_interaction(self):
        pass

    def _apply_combat(self):
        pass

    def get_strut_hitboxes(self):
        strut_hitboxes = []
        for strut_conf in self.strutsets.values():
            sets = strut_conf['sets']
            for strut in sets:
                strut_hitboxes.append(strut.get('hitbox'))
        return strut_hitboxes

    def get_hero_hitbox(self):
        static_hero_props = self.sprite_property_conf['hero']
        hero_hitbox = (
            self.hero['position']['x'] + static_hero_props['hitbox'][0], 
            self.hero['position']['y'] + static_hero_props['hitbox'][1],
            static_hero_props['hitbox'][2],
            static_hero_props['hitbox'][3]
        )
        return hero_hitbox

    def get_sprite_hitboxes(self, key):
        calculated = []

        if key == 'npcs':
            iter_set = self.npcs
        elif key == 'villains':
            iter_set = self.villains
        else:
            iter_set = []

        for sprite_key, sprite_conf in iter_set.items():
            raw_hitbox = self.sprite_property_conf[sprite_key]['hitbox']
            sprite_pos = sprite_conf['position']['x'], sprite_conf['position']['y']
            calc_hitbox = (
                sprite_pos[0] + raw_hitbox[0],
                sprite_pos[1] + raw_hitbox[1],
                raw_hitbox[2],
                raw_hitbox[3]
            )
            calculated.append(calc_hitbox)
        return calculated
    
    def get_strutsets(self):
        return { key: val for key, val in self.strutsets.items() if key != 'hitboxes' } 

    def get_tilesets(self):
        return self.tilesets

    def save(self):
        dynamic_conf = self.hero.copy()
        # dynamic_conf.update(self.other_conf)
        state.save_state('dynamic', dynamic_conf)

    def iterate(self, user_input: dict) -> dict:
        """
        Update the world state.
        """
        self._update_npcs()
        self._update_hero(user_input)
        self._apply_physics()
        self._apply_combat()
        self._apply_interaction()