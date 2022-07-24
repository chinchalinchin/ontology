
from logging.config import valid_ident
import onta.settings as settings
import onta.load.state as state
import onta.load.conf as conf
import onta.util.logger as logger
import onta.engine.calculator as calculator
import onta.engine.collisions as collisions
import onta.engine.paths as paths

log = logger.Logger('onta.world', settings.LOG_LEVEL)

class World():

    composite_conf = None
    """
    """
    plate_property_conf = None
    """
    """
    strut_property_conf = None
    """
    Holds strut property configuration information
    ```python
    self.strut_property_conf = {
            'strut_1': {
                'hitbox_1': hitbox_dim, # tuple
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
            'blocking_states': [ block_state_1, block_state_2, ], # list(str)
            # ...
        },
    }
    ```
    """
    tilesets = None
    """
    ```python
    self.tilesets = {
        'layer_1': {
            'tile_1': {
                'sets': [
                    { 
                        'start': {
                            'tile_units': tile_units, # bool
                            'x': x, # int
                            'y': y, # int
                        },
                        'cover': cover, # bool
                    }
                ]
            },
        }
    }
    ```
    """
    strutsets = None
    """
    ```python
    self.strutsets = {
        'layer_1': {
            'strut_1': {
                'sets': [
                    { 
                        'start': {
                            'tile_units': tile_units, # bool
                            'x': x, # int
                            'y': y, # int
                        },
                        'cover': cover, # bool
                        'hitbox': (hx, hy, hw, hh), # tuple(int, int, int, int)

                    }
                ]
            },
        },
    }
    ```
    """
    platesets = None
    """
    ```python
    self.platesets = {
        'layer_1': {
            'strut_1': {
                'sets': [
                    { 
                        'start': {
                            'tile_units': tile_units, # bool
                            'x': x, # int
                            'y': y, # int
                        },
                        'hitbox': (hx, hy, hw, hh), # tuple(int, int, int, int)
                        'cover': cover, # bool
                        'door': {
                            'layer': layer, # str
                        },
                    }
                ]
            },
        },
    }
    ```
    """
    compositions = None
    """
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
    iterations = 0

    def __init__(self, config: conf.Conf, state_ao: state.State) -> None:
        """
        Creates an instance of `onta.world.World` and calls internal methods to initialize in-game element configuration, the game's static state and the game's dynamic state.

        .. notes:
            - Configuration and state are passed in to populate internal dictionaries. No references are kept to the `config` or `state_ao` objects.
        """
        self._init_conf(config)
        self._init_static_state(state_ao)
        self._generate_composite_static_state()
        self._init_dynamic_state(state_ao)
        self._init_stationary_hitboxes()

    def _init_conf(self, config: conf.Conf) -> None:
        """ 
        Initialize configuration properties for in-game elements in the memory.
        """
        unpack = config.load_sprite_configuration()
        self.sprite_state_conf, self.sprite_property_conf, _ = unpack
        self.plate_property_conf, _ = config.load_plate_configuration()
        self.strut_property_conf, _ = config.load_strut_configuration()
        self.composite_conf = config.load_composite_configuration()

    def _init_static_state(self, state_ao: state.State) -> None:
        """
        Initialize the state for static in-game elements, i.e. elements that do not move and are not interactable.
        """
        log.debug(f'Initializing simple static world state...', 'World._init_static_state')
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
        self.tilesets, self.strutsets = {}, {}
        self.platesets, self.compositions = {}, {}
        for layer_key, layer_conf in static_conf['layers'].items():
            self.layers.append(layer_key)
            self.tilesets[layer_key] = layer_conf.get('tiles')
            self.strutsets[layer_key] = layer_conf.get('struts')
            self.platesets[layer_key] = layer_conf.get('plates')
            self.compositions[layer_key] = layer_conf.get('compositions')

    def _generate_composite_static_state(self) -> None:
        log.debug(f'Decomposing composite static world state into constituents...', 'World._generate_composite_static_state')

        for layer in self.layers:
            layer_compositions = self.compositions[layer]
            if layer_compositions is not None:
                for composite_key, composition in layer_compositions.items():
                    # NOTE: composition = { 'order': int, 'sets': [ ... ] }
                    #           via compose state information (static.yaml)
                    compose_sets = composition['sets']

                    # NOTE: compose_conf = { 'struts': { ..}, 'plates': { ...} }
                    #           via compose configuration information (composite.yaml)
                    compose_conf = self.composite_conf[composite_key]

                    log.verbose(f'Decomposing {composite_key} composition...', 'World._generate_composite_static_state')

                    for composeset in compose_sets:
                        # NOTE: compose_set = { 'start': { ... } }
                        #           via compose state information (static.yaml)
                        if composeset['start']['tile_units'] == 'absolute':
                            compose_start = (
                                composeset['start']['x'], 
                                composeset['start']['y']
                            )
                        else:
                            compose_start =(
                                composeset['start']['x']*settings.TILE_DIM[0],
                                composeset['start']['y']*settings.TILE_DIM[1]
                            )

                        for elementset_key, elementset in compose_conf.items():

                            log.verbose(f'Initializing decomposed {elementset_key} elementset...', 'World._generate_composite_static_state')

                            # NOTE: elementset = { 'element_key': { 'order': int, 'sets': [ ... ] } }
                            #           via compose element configuration (composite.yaml)
                            for element_key, element in elementset.items():
                                
                                log.verbose(f'Initializing {element_key}', 'World._generate_composite_static_state')

                                # NOTE: element_sets = [ { 'start': {..}, 'cover': bool } ]
                                #            via compose element configuration (composite.yaml)
                                element_sets = element['sets']

                                # TODO: adjust strutset rendering order based on element order

                                if elementset_key == 'struts':

                                    for strutset in element_sets:
                                        # NOTE strutset = { 'start': { ... }, 'cover': bool }
                                        #       via compose element configuration (composite.yaml)
                                        if self.strutsets[layer][element_key]['sets'] is None:
                                            self.strutsets[layer][element_key]['sets'] = []

                                        self.strutsets[layer][element_key]['sets'].append(
                                            {
                                                'start': {
                                                    'tile_units': strutset['start']['tile_units'],
                                                    'x': compose_start[0] + strutset['start']['x'],
                                                    'y': compose_start[1] + strutset['start']['y'],
                                                },
                                                'cover': strutset['cover'],
                                            }
                                        )

                                # TODO: adjust plateset rendering order based on element order

                                elif elementset_key == 'plates':

                                    for plateset in element_sets:
                                        # NOTE plateset = { 'start': { ... }, 'cover': bool }
                                        #       via compose element configuration (composite.yaml)
                                        if self.platesets[layer][element_key]['sets'] is None:
                                            self.platesets[layer][element_key]['sets'] = []
                                            
                                        self.platesets[layer][element_key]['sets'].append(
                                            {
                                                'start': {
                                                    'tile_units': 'absolute',
                                                    'x': compose_start[0] + plateset['start']['x'],
                                                    'y': compose_start[1] + plateset['start']['y']
                                                },
                                                'cover': plateset['cover'],
                                                'door': plateset.get('door')
                                            }
                                        )



    def _init_dynamic_state(self, state_ao: state.State) -> None:
        """
        Initialize the state for dynamic in-game elements, i.e. elements that move and are interactable.
        """
        log.debug(f'Initalizing dynamic world state...', 'World._init_dynamic_state')
        dynamic_conf = state_ao.get_state('dynamic')
        self.hero = dynamic_conf['hero']
        self.layer = dynamic_conf['hero']['layer']
        self.npcs = dynamic_conf.get('npcs') if dynamic_conf.get('npcs') is not None else {}
        self.villains = dynamic_conf.get('villains') if dynamic_conf.get('villains') is not None else {}

    def _init_stationary_hitboxes(self) -> None:
        """
        Construct static hitboxes from object dimensions and properties.

        .. notes:
            - All of the strut hitboxes are condensed into a list in `self.strutsets['hitboxes']`, so that strut hitboxes only need calculated once.
            - Strut
        """
        log.debug(f'Calculating stationary hitbox locations...', 'World._init_stationary_hitboxes')
        for layer in self.layers:

            # if self.platesets[layer] is None:
            #     self.platesets[layer] = {}
            # if self.strutsets[layer] is None:
            #     self.strutsets[layer] = {}

            for static_set in ['strutset', 'plateset']:

                if static_set == 'strutset':
                    iter_set = self.get_strutsets(layer).copy()
                    props = self.strut_property_conf
                elif static_set == 'plateset':
                    iter_set = self.get_platesets(layer).copy()
                    props = self.plate_property_conf
                
                for set_key, set_conf in iter_set.items():
                    set_props = props[set_key]

                    log.debug(f'Initializing {static_set} {set_key} hitboxes with properties: {set_props}', 'World._init_hitboxes')

                    for i, set_conf in enumerate(set_conf['sets']):

                        if set_props['hitbox'] is not None:
                            if set_conf['start']['tile_units'] == 'default':
                                x = set_conf['start']['x']*settings.TILE_DIM[0]
                                y = set_conf['start']['y']*settings.TILE_DIM[1]
                            if set_conf['start']['tile_units'] == 'relative':
                                x = set_conf['start']['x']*set_props['size']['w']
                                y = set_conf['start']['y']*set_props['size']['h']
                            else:
                                x, y = set_conf['start']['x'], set_conf['start']['y']
                            
                            hitbox = (
                                x + set_props['hitbox']['offset']['x'], 
                                y + set_props['hitbox']['offset']['y'],
                                set_props['hitbox']['size']['w'], 
                                set_props['hitbox']['size']['h']
                            )
                            if static_set == 'strutset' :
                                self.strutsets[layer][set_key]['sets'][i]['hitbox'] = hitbox
                            elif static_set == 'plateset':
                                self.platesets[layer][set_key]['sets'][i]['hitbox'] = hitbox
                        else:
                            if static_set == 'strutset':
                                self.strutsets[layer][set_key]['sets'][i]['hitbox'] = None
                            elif static_set == ['plateset']:
                                self.platesets[layer][set_key]['sets'][i]['hitbox'] = None
            
            # condense all the hitboxes into a list and save to strutsets,
            # to avoid repeated internal calls to `get_strut_hitboxes`
            world_bounds = [
                (0, 0, self.dimensions[0], 1), 
                (0, 0, 1, self.dimensions[1]),
                (self.dimensions[0], 0, 1, self.dimensions[1]),
                (0, self.dimensions[1], self.dimensions[0], 1)
            ]
            self.strutsets[layer]['hitboxes'] = world_bounds + self.get_strut_hitboxes(layer)
            self.platesets[layer]['doors'] = self.get_doors(layer)

    def _update_hero(self, user_input: dict) -> None: 
        """
        Map user input to new hero state, apply state action and iterate state frame.
        """
        if self.hero['state'] not in self.sprite_property_conf['hero']['blocking_states']:
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

        if self.hero['frame'] >= self.sprite_state_conf['hero'][self.hero['state']]['frames']:
            self.hero['frame'] = 0

    def _update_npcs(self) -> None:
        """
        Maps npc state to in-game action, applies action and then iterates npc state frame.

        .. notes:
            - This method is essentially an interface between the NPC state and the game world. It determines what happens to an NPC once it is in a state.
        """
        for npc_key, npc in self.npcs.items():
            npc_props = self.sprite_property_conf[npc_key]

            if npc['state'] not in self.sprite_property_conf[npc_key]['blocking_states']:
                if 'run' in npc['state']:
                    speed = npc_props['run']
                else:
                    speed = npc_props['walk']

                if npc['state'] == 'walk_up':
                    npc['position']['y'] -= speed
                elif npc['state'] == 'walk_left':
                    npc['position']['x'] -= speed
                elif npc['state'] == 'walk_right':
                    npc['position']['x'] += speed
                elif npc['state'] == 'walk_down':
                    npc['position']['y'] += speed

            npc['frame'] += 1

            if self.iterations % npc_props['poll'] == 0:
                self._reorient('npcs', npc_key)

            if npc['frame'] >= self.sprite_state_conf[npc_key][npc['state']]['frames']:
                npc['frame'] = 0
    
    def _reorient(self, spriteset_key, sprite_key) -> None:
        if spriteset_key == 'npcs':
            sprite = self.npcs[sprite_key]
        elif spriteset_key == 'villains':
            sprite = self.villains[sprite_key]

        sprite_hitbox = self.get_sprite_hitbox(spriteset_key, 'strut', sprite_key)
        vil_hitboxes = self.get_sprite_hitboxes('villains', 'strut', sprite['layer'], [sprite_key])
        npc_hitboxes = self.get_sprite_hitboxes('npcs', 'strut', sprite['layer'], [sprite_key])

        collision_sets = []
        if npc_hitboxes is not None:
            collision_sets.append(npc_hitboxes)
        if vil_hitboxes is not None:
            collision_sets.append(vil_hitboxes)
        if self.strutsets[sprite['layer']]['hitboxes'] is not None:
            collision_sets.append(self.strutsets[sprite['layer']]['hitboxes'])
        
        paths.reorient(
            sprite,
            sprite_hitbox,
            collision_sets, 
            self.sprite_property_conf[sprite_key]['paths'][sprite['path']],
            self.sprite_property_conf[sprite_key]['collide'],
            self.dimensions
        )

    def _apply_physics(self) -> None:
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

                        collision_sets = []
                        if hitbox_key =='sprite':
                            npc_hitboxes = self.get_sprite_hitboxes('npcs', hitbox_key, sprite['layer'], exclusions)
                            vil_hitboxes = self.get_sprite_hitboxes('villains', hitbox_key, sprite['layer'], exclusions)

                            if npc_hitboxes is not None:
                                collision_sets.append(npc_hitboxes)
                            if vil_hitboxes is not None:
                                collision_sets.append(vil_hitboxes)

                        if hitbox_key == 'strut' and self.strutsets[sprite['layer']]['hitboxes'] is not None:
                            collision_sets.append(self.strutsets[sprite['layer']]['hitboxes'])

                        log.infinite(f'Checking {spriteset_key} set member "{sprite_key}" with hitbox {sprite_hitbox} for {hitbox_key} collisions...', 
                            '_apply_physics')

                        collided = False
                        for collision_set in collision_sets:
                            if collisions.detect_collision(
                                sprite_hitbox, 
                                collision_set
                            ):
                                collided =True
                                collisions.recoil_sprite(
                                    sprite, 
                                    self.sprite_property_conf[sprite_key]
                                )
                        if collided:
                                # recalculate hitbox after sprite recoils
                            sprite_hitbox = self.get_sprite_hitbox(spriteset_key, hitbox_key, sprite_key)
                            paths.reorient(
                                sprite,
                                sprite_hitbox,
                                collision_sets, 
                                self.sprite_property_conf[sprite_key]['paths'][sprite['path']],
                                self.sprite_property_conf[sprite_key]['collide'],
                                self.dimensions
                            )

                        for key, val in collision_map.copy().items():
                            if key not in exclusions and key == sprite_key:
                                for nest_key in val.keys():
                                    collision_map[key][nest_key] = True
                                    collision_map[nest_key][key] = True
    
                elif spriteset_key == 'hero':
                    sprite_hitbox = self.get_sprite_hitbox(spriteset_key, 'sprite', sprite_key)
                    vil_hitboxes = self.get_sprite_hitboxes('villains', 'sprite', self.layer)
                    npc_hitboxes = self.get_sprite_hitboxes('npcs', 'sprite', self.layer)

                    collision_sets = []
                    if npc_hitboxes is not None:
                        collision_sets.append(npc_hitboxes)
                    if vil_hitboxes is not None:
                        collision_sets.append(vil_hitboxes)
                    if self.strutsets[self.layer]['hitboxes'] is not None:
                        collision_sets.append(self.strutsets[sprite['layer']]['hitboxes'])

                    log.infinite('Checking "hero" for collisions...', '_apply_physics')

                    for collision_set in collision_sets:
                        if collisions.detect_collision(sprite_hitbox, collision_set):
                            collisions.recoil_sprite(sprite, self.sprite_property_conf[sprite_key])
    
    def _apply_interaction(self, user_input: dict):
        if user_input['interact']:
            doors = self.platesets[self.layer]['doors']

            for door in doors:
                door_hitbox = door['hitbox']
                hero_hitbox = self.get_sprite_hitbox('hero', 'sprite', 'hero')
                if collisions.detect_collision(hero_hitbox, [ door_hitbox ]):
                    self.layer = door['layer']

    def _apply_combat(self):
        pass

    def get_strut_hitboxes(self, layer):
        strut_hitboxes = []
        for strut_conf in self.get_strutsets(layer).values():
            sets = strut_conf['sets']
            for strut in sets:
                strut_hitboxes.append(strut['hitbox'])
        return strut_hitboxes

    def get_doors(self, layer):
        doors = []
        for plate_key, plate_conf in self.get_platesets(layer).items():
            if self.plate_property_conf[plate_key]['door']:
                sets = plate_conf['sets']
                for plate in sets:
                    doors.append({
                        'hitbox': plate['hitbox'],
                        'layer': plate['door']['layer']
                    })
        return doors

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

    def get_sprite_hitboxes(self, spriteset, hitbox_key, layer, exclude = None):
        calculated = []

        if spriteset == 'npcs':
            iter_set = self.get_npcs(layer)
        elif spriteset == 'villains':
            iter_set = self.get_villains(layer)
        else:
            iter_set = {}

        for sprite_key in iter_set.keys():
            if exclude is None or sprite_key not in exclude:
                if spriteset == 'npcs':
                    calculated.append(self.get_sprite_hitbox('npcs', hitbox_key, sprite_key))
                elif spriteset == 'villains':
                    calculated.append(self.get_sprite_hitbox('villains', hitbox_key, sprite_key))
        return calculated
    
    def get_strutsets(self, layer):
        iter_set = self.strutsets[layer].items() if self.strutsets[layer] is not None else { }
        return {
            key: val
            for key, val in iter_set
            if key not in  ['hitboxes'] 
        }

    def get_platesets(self, layer):
        iter_set = self.platesets[layer].items() if self.platesets[layer] is not None else { }
        return {
            key: val
            for key, val in iter_set
            if key not in ['doors']
        }

    def get_npcs(self, layer):
        return {
            key: val
            for key, val 
            in self.npcs.items()
            if val['layer'] == layer
        }

    def get_villains(self, layer):
        return {
            key: val
            for key, val in self.villains.items()
            if val['layer'] == layer
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
        self.iterations += 1