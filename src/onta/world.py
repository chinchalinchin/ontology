
from logging.config import valid_ident
import onta.settings as settings
import onta.load.state as state
import onta.load.conf as conf
import onta.util.logger as logger
import onta.engine.calculator as calculator
import onta.engine.collisions as collisions

log = logger.Logger('onta.world', settings.LOG_LEVEL)

class World():

    # TODO: possibly. does it make sense to separate property and state conf for sprites?

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
        },
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
            'size': (w, h), # tuple
            'hitbox': (offset_x, offset_y, width, height), # tuple
        },
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
        },
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
        },
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
    layer = None
    layers = None
    doors = None

    def __init__(self, config: conf.Conf, state_ao: state.State):
        """
        Creates an instance of `onta.world.World` and calls internal methods to initialize in-game element configuration, the game's static state and the game's dynamic state.

        .. notes:
            - Configuration and state are passed in to populate internal dictionaries. No references are kept to the `config` or `state_ao` objects.
        """
        self._init_conf(config)
        self._init_static_state(state_ao)
        self._init_dynamic_state(state_ao)

    def _init_conf(self, config: conf.Conf):
        """ 
        Initialize configuration properties for in-game elements in the memory.
        """
        struts_conf = config.configuration('struts')
        sprites_conf = config.configuration('sprites')

        self.sprite_state_conf = {}
        self.sprite_property_conf = {}
        for sprite_key, sprite_conf in sprites_conf.items():
            self.sprite_state_conf[sprite_key] = {}
            self.sprite_property_conf[sprite_key] = {}

            self.sprite_property_conf[sprite_key] = sprite_conf['properties']
            self.sprite_property_conf[sprite_key]['size'] = sprite_conf['size']

            self.sprite_state_conf[sprite_key]['blocking_states'] = sprite_conf['blocking_states']
            for state_map in sprite_conf['states']:
                state = list(state_map.keys())[0]
                self.sprite_state_conf[sprite_key][state] = state_map[state]['frames']

        self.strut_property_conf = {}
        
        for strut_key, strut_conf in struts_conf.items():
            self.strut_property_conf[strut_key] = {}
            self.strut_property_conf[strut_key]['size'] = strut_conf['image']['size']
            self.strut_property_conf[strut_key]['hitbox'] = strut_conf['properties']['hitbox']
            self.strut_property_conf[strut_key]['door'] = strut_conf['properties']['door']

    def _init_static_state(self, state_ao: state.State):
        """
        Initialize the state for static in-game elements, i.e. elements that do not move and are not interactable.
        """
        static_conf = state_ao.get_state('static')

        if static_conf['properties']['size']['tile_units'] == 'relative':
            self.dimensions = (
                static_conf['properties']['size']['w']*settings.TILE_DIM[0], 
                static_conf['properties']['size']['h']*settings.TILE_DIM[1]
            )
        else:
            self.dimensions =(
                static_conf['properties']['size']['w'],
                static_conf['properties']['size']['h']
            )

        self.layers = []
        self.tilesets, self.strutsets = { }, { }
        for layer_key, layer_conf in static_conf['layers'].items():
            self.layers.append(layer_key)
            self.tilesets[layer_key] = layer_conf.get('tiles')
            self.strutsets[layer_key] = layer_conf.get('struts')

        self._init_static_hitboxes()
        log.debug(f'Initialized static world layer with dimensions {self.dimensions}', 'World._init_static_layer')

    def _init_dynamic_state(self, state_ao: state.State):
        """
        Initialize the state for dynamic in-game elements, i.e. elements that move and are interactable.
        """
        dynamic_conf = state_ao.get_state('dynamic')
        self.hero = dynamic_conf['hero']
        self.layer = dynamic_conf['hero']['layer']
        self.npcs = dynamic_conf.get('npcs') if dynamic_conf.get('npcs') is not None else {}
        self.villains = dynamic_conf.get('villains') if dynamic_conf.get('villains') is not None else {}

    def _init_static_hitboxes(self):
        """
        Construct static hitboxes from object dimensions and properties.
        """
        for layer in self.layers:
            buffer_strutsets = self.strutsets[layer].copy()

            for strutset_key, strutset_conf in buffer_strutsets.items():
                strutset_props = self.strut_property_conf[strutset_key]

                log.debug(f'Initialize strutset {strutset_key} with properties: {strutset_props}', 'World._init_hitboxes')

                for i, strut_conf in enumerate(strutset_conf['sets']):

                    if strutset_props['hitbox'] is not None:
                        if strut_conf['start']['tile_units'] == 'default':
                            x = strut_conf['start']['x']*settings.TILE_DIM[0]
                            y = strut_conf['start']['y']*settings.TILE_DIM[1]
                        if strut_conf['start']['tile_units'] == 'relative':
                            x = strut_conf['start']['x']*strutset_props['size']['w']
                            y = strut_conf['start']['y']*strutset_props['size']['h']
                        else:
                            x, y = strut_conf['start']['x'], strut_conf['start']['y']
                        
                        top_x = x + strutset_props['hitbox']['offset']['x']
                        top_y = y + strutset_props['hitbox']['offset']['y']
                        
                        self.strutsets[layer][strutset_key]['sets'][i]['hitbox'] = (
                            top_x, 
                            top_y,
                            strutset_props['hitbox']['size']['w'], 
                            strutset_props['hitbox']['size']['h']
                        )
                    else:
                        self.strutsets[layer][strutset_key]['sets'][i]['hitbox'] = None
        
            # condense all the hitboxes into a list and save to strutsets,
            # to avoid repeated internal calls to `get_strut_hitboxes`
            self.strutsets[layer]['hitboxes'] = self.get_strut_hitboxes(layer, False)
            self.strutsets[layer]['doors'] = self.get_strut_hitboxes(layer, True)

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
        if len(self.npcs) > 0:
            for npc_key, npc in self.npcs.items():
                npc_props = self.sprite_property_conf[npc_key]

                if npc['state'] not in self.sprite_state_conf[npc_key]['blocking_states']:
                    if 'run' in npc['state']:
                        speed = npc_props['run']
                    else:
                        speed = npc_props['walk']

                    if npc['state'] == 'walk_up':
                        npc['position']['y'] -= speed
                    elif npc['state'] == 'walk_left':
                        npc['position']['x'] -= speed
                    elif npc['state'] == 'walk_right':
                        npc['position']['y'] += speed
                    elif npc['state'] == 'walk_down':
                        npc['position']['y'] += speed

                npc['frame'] += 1

                if npc['frame'] >= self.sprite_state_conf[npc_key][npc['state']]:
                    npc['frame'] = 0

                # TODO: hit detection

    def _apply_physics(self):
        """
        
        .. notes:
            - Keep in mind, the sprite collision doesn't care what sprite or strut with which the player collided, only what direction the player was travelling when the collision happened. The door hit detection, however, _is_ aware of what door with which the player is colliding, in order to locate the world layer to which the door is connected.
            - Technically, there is overlap here. Since sprite npc is checked against every other sprite for collisions, there are Pn = n!/(n-2)! permutations, but Cn = n!/(2!(n-2)!). Therefore, Pn - Cn checks are unneccesary. To circumvent this problem (sort of), a collision map is kept internally within this method to keep track of which sprite-to-sprite collisions have already taken place. However, whether or not this is worth the effort, since the map has to be traversed when it is initialized.
        """

        collision_map = { 
            npc_key: {
                vil_key: False for vil_key in self.villains.keys()
            } for npc_key in self.npcs.keys()
        }
        collision_map.update({
            vil_key: {
                npc_key: False for npc_key in self.npcs.keys()
            } for vil_key in self.villains.keys()
        })

        for spriteset_key in ['hero', 'npcs', 'villains']:
            if spriteset_key == 'hero':
                iter_set = { 'hero': self.hero }
            elif spriteset_key == 'npcs':
                iter_set = self.npcs
            elif spriteset_key == 'villains':
                iter_set = self.villains

            for sprite_key, sprite in iter_set.items():
                if spriteset_key in ['npcs', 'villains']:
                    for hitbox_key in ['sprite', 'strut']:

                        exclusions = [ sprite_key ]
                        for key, val in collision_map[sprite_key].items():
                            if val:
                                exclusions.append(key)

                        sprite_hitbox = self.get_sprite_hitbox(spriteset_key, hitbox_key, sprite_key)
                        vil_hitboxes = self.get_sprite_hitboxes('villains', hitbox_key, exclusions)
                        npc_hitboxes = self.get_sprite_hitboxes('npcs', hitbox_key, exclusions)

                        collision_sets = [npc_hitboxes, vil_hitboxes, self.strutsets[self.layer]['hitboxes']]

                        log.verbose(f'Checking {spriteset_key} set member "{sprite_key}" with hitbox {sprite_hitbox} for {hitbox_key} collisions...', 
                            '_apply_physics')


                        for collision_set in collision_sets:
                            if collisions.detect_collision(sprite_hitbox, collision_set):
                                collisions.recoil_sprite(sprite, self.sprite_property_conf[sprite_key])

                        for key, val in collision_map.copy().items():
                            if key not in exclusions and key == sprite_key:
                                for nest_key in val.keys():
                                    collision_map[key][nest_key] = True
                                    collision_map[nest_key][key] = True
    
                elif spriteset_key == 'hero':
                    sprite_hitbox = self.get_sprite_hitbox(spriteset_key, sprite_key, sprite_key)
                    vil_hitboxes = self.get_sprite_hitboxes('villains', sprite_key)
                    npc_hitboxes = self.get_sprite_hitboxes('npcs', sprite_key)

                    log.verbose('Checking "hero" for collisions...', 
                        '_apply_physics')

                    collision_sets = [npc_hitboxes, vil_hitboxes, self.strutsets[self.layer]['hitboxes']]
                    for collision_set in collision_sets:
                        if collisions.detect_collision(sprite_hitbox, collision_set):
                            collisions.recoil_sprite(sprite, self.sprite_property_conf[sprite_key])
    
    def _apply_interaction(self, user_input: dict):
        if user_input['interact']:
            doors = self.strutsets[self.layer]['doors']

    def _apply_combat(self):
        pass

    def get_strut_hitboxes(self, layer, door = False):
        strut_hitboxes = []
        for strut_conf in self.get_strutsets(layer, door).values():
            sets = strut_conf['sets']
            for strut in sets:
                strut_hitboxes.append(strut.get('hitbox'))
        return strut_hitboxes

    def get_sprite_hitbox(self, spriteset, hitbox_key, sprite_key):
        """
        .. notes:
            - A sprite's hitbox dimensions are fixed, but the actual hitbox coordinates depend on the position of the sprite. This method must be called each iteration of the world loop, so the newest coordinates of the hitbox are retrieved.
        """
        if spriteset == 'hero':
            sprite = self.hero
        elif spriteset == 'npcs':
            sprite = self.npcs.get(sprite_key)
        elif spriteset == 'villains':
            sprite = self.villains.get(sprite_key)
        if sprite is not None:
            raw_hitbox = self.sprite_property_conf[sprite_key]['hitboxes'][hitbox_key]
            calc_hitbox = (
                sprite['position']['x'] + raw_hitbox['offset']['x'],
                sprite['position']['y'] + raw_hitbox['offset']['y'],
                raw_hitbox['size']['w'],
                raw_hitbox['size']['h']
            )
            return calc_hitbox
        return None

    def get_sprite_hitboxes(self, spriteset, hitbox_key, exclude = None):
        calculated = []

        if spriteset == 'npcs':
            iter_set = self.npcs
        elif spriteset == 'villains':
            iter_set = self.villains
        else:
            iter_set = {}

        for sprite_key in iter_set.keys():
            if exclude is None or sprite_key not in exclude:
                if spriteset == 'npcs':
                    calculated.append(self.get_sprite_hitbox('npcs', hitbox_key, sprite_key))
                elif spriteset == 'villains':
                    calculated.append(self.get_sprite_hitbox('villains', hitbox_key, sprite_key))
        return calculated
    
    def get_strutsets(self, layer, doors = False):
        return {
            key: val
            for key, val in self.strutsets[layer].items()
            if key not in  ['hitboxes', 'doors'] 
                and self.strut_property_conf[key]['door'] == doors
        }

    def get_tilesets(self, layer: str):
        return self.tilesets[layer] if self.tilesets[layer] is not None else { }

    def save(self, state_ao: state.State):
        self.hero['layer'] = self.layer
        dynamic_conf = {
            'hero': self.hero,
            'npcs': self.npcs,
            'villains': self.villains
        }
        state_ao.save_state('dynamic', dynamic_conf)

    def iterate(self, user_input: dict) -> dict:
        """
        Update the world state.
        """

        self._update_npcs()
        self._update_hero(user_input)
        self._apply_physics()
        self._apply_combat()
        self._apply_interaction(user_input)