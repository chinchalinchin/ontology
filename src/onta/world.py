
from logging.config import valid_ident
from re import S
import onta.settings as settings
import onta.load.state as state
import onta.load.conf as conf
import onta.util.logger as logger
import onta.engine.calculator as calculator
import onta.engine.collisions as collisions
import onta.engine.paths as paths

log = logger.Logger('onta.world', settings.LOG_LEVEL)

class World():

    # CONFIGURATION FIELDS
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

    # OBJECT SET FIELDS
    tilesets = None
    """
    ```python
    self.tilesets = {
        'layer_1': {
            'tile_1': {
                'sets': [
                    { 
                        'start': {
                            'units': units, # bool
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
                            'units': units, # bool
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
                            'units': units, # bool
                            'x': x, # int
                            'y': y, # int
                        },
                        'hitbox': (hx, hy, hw, hh), # tuple(int, int, int, int)
                        'cover': cover, # bool
                        'content': content, # str
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

    dimensions = None
    """
    ```
    self.dimensions = (w, h) # tuple
    ```
    """
    tile_dimensions = None
    """
    """
    layer = None
    layers = None
    doors = None
    switch_map = None
    iterations = 0

    def __init__(self, ontology_path: str = settings.DEFAULT_DIR) -> None:
        """
        Creates an instance of `onta.world.World` and calls internal methods to initialize in-game element configuration, the game's static state and the game's dynamic state.

        .. notes:
            - Configuration and state are passed in to populate internal dictionaries. No references are kept to the `config` or `state_ao` objects.
        """
        config = conf.Conf(ontology_path)
        state_ao = state.State(ontology_path)
        self._init_conf(config)
        self._init_static_state(state_ao)
        self._generate_composite_static_state()
        self._generate_stationary_hitboxes()
        self._generate_switch_map()
        self._init_dynamic_state(state_ao)


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

        self.tile_dimensions = (static_conf['world']['tiles']['w'], static_conf['world']['tiles']['h'])
        self.dimensions = calculator.scale(
            (static_conf['world']['size']['w'], static_conf['world']['size']['h']),
            self.tile_dimensions,
            static_conf['world']['size']['units']
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
        """_summary_

        .. notes:
            - Method must be called before stationary hitboxes are initialized, since this method decompose compositions into their consistuent sets and appends them to the existing static state.

        """
        log.debug(f'Decomposing composite static world state into constituents...', 'World._generate_composite_static_state')

        import pprint

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
                        compose_start = calculator.scale(
                            (composeset['start']['x'], composeset['start']['y']),
                            self.tile_dimensions,
                            composeset['start']['units']
                        )

                        for elementset_key, elementset_conf in compose_conf.items():

                            log.verbose(f'Initializing decomposed {elementset_key} elementset...', 'World._generate_composite_static_state')

                            # NOTE: elementset = { 'element_key': { 'order': int, 'sets': [ ... ] } }
                            #           via compose element configuration (composite.yaml)
                            for element_key, element in elementset_conf.items():
                                
                                log.verbose(f'Initializing {element_key}', 'World._generate_composite_static_state')

                                # NOTE: element_sets = [ { 'start': {..}, 'cover': bool } ]
                                #            via compose element configuration (composite.yaml)
                                element_sets = element['sets']

                                # TODO: adjust strutset rendering order based on element order

                                buffer_sets = self.get_formsets(elementset_key).copy()

                                for elementset in element_sets:

                                    log.verbose('Generating strut render order', 'World._generate_composite_static_state')
                                    
                                    # NOTE strutset = { 'start': { ... }, 'cover': bool }
                                    #       via compose element configuration (composite.yaml)

                                    if buffer_sets.get(layer) is None:
                                        buffer_sets[layer] = {}
                                    
                                    if buffer_sets[layer].get(element_key) is None:
                                        buffer_sets[layer][element_key] = {}

                                    if buffer_sets[layer][element_key].get('sets') is None:
                                        buffer_sets[layer][element_key]['sets'] = []
                                    
                                    if buffer_sets[layer][element_key].get('order') is None:
                                        buffer_sets[layer][element_key]['order'] = len(buffer_sets[layer]) - 1

                            
                                    if elementset_key == 'plates':
                                        buffer_sets[layer][element_key]['sets'].append(
                                            {
                                                'start': {
                                                    'units': elementset['start']['units'],
                                                    'x': compose_start[0] + elementset['start']['x'],
                                                    'y': compose_start[1] + elementset['start']['y'],
                                                },
                                                'cover': elementset['cover'],
                                                'content': elementset['content']

                                            }
                                        )
                                    else:
                                        buffer_sets[layer][element_key]['sets'].append(
                                            {
                                                'start': {
                                                    'units': elementset['start']['units'],
                                                    'x': compose_start[0] + elementset['start']['x'],
                                                    'y': compose_start[1] + elementset['start']['y'],
                                                },
                                                'cover': elementset['cover'],
                                            }
                                        )
                                
                                if elementset_key == 'tiles':
                                    self.tilesets = buffer_sets
                                elif elementset_key == 'struts':
                                    self.strutsets = buffer_sets
                                elif elementset_key == 'plates':
                                    self.platesets = buffer_sets


    def _generate_stationary_hitboxes(self) -> None:
        """
        Construct static hitboxes from object dimensions and properties.

        .. notes:
            - All of the strut hitboxes are condensed into a list in `self.strutsets['hitboxes']`, so that strut hitboxes only need calculated once.
            - Strut
        """
        log.debug(f'Calculating stationary hitbox locations...', 'World._init_stationary_hitboxes')
        for layer in self.layers:
            for static_set in ['strutset', 'plateset']:

                if static_set == 'strutset':
                    iter_set = self.get_strutsets(layer).copy()
                    props = self.strut_property_conf
                elif static_set == 'plateset':
                    iter_set = self.get_platesets(layer).copy()
                    props = self.plate_property_conf
                
                for set_key, set_conf in iter_set.items():
                    log.debug(f'Initializing {static_set} {set_key} hitboxes', 'World._init_hitboxes')

                    set_props, set_hitbox = props[set_key], props[set_key]['hitbox']

                    for i, set_conf in enumerate(set_conf['sets']):

                        set_hitbox = collisions.calculate_set_hitbox(
                            set_props['hitbox'], 
                            set_conf, 
                            self.tile_dimensions
                        )
                        if static_set == 'strutset' :
                            self.strutsets[layer][set_key]['sets'][i]['hitbox'] = set_hitbox
                        elif static_set == 'plateset':
                            self.platesets[layer][set_key]['sets'][i]['hitbox'] = set_hitbox
            
            # condense all the hitboxes into a list and save to strutsets,
            # to avoid repeated internal calls to `get_strut_hitboxes`
            world_bounds = [
                (0, 0, self.dimensions[0], 1), 
                (0, 0, 1, self.dimensions[1]),
                (self.dimensions[0], 0, 1, self.dimensions[1]),
                (0, self.dimensions[1], self.dimensions[0], 1)
            ]
            self.strutsets[layer]['hitboxes'] = world_bounds + self.get_strut_hitboxes(layer)
            self.platesets[layer]['doors'] = self.get_typed_platesets(layer, 'door')
            self.platesets[layer]['containers'] = self.get_typed_platesets(layer, 'container')
            self.platesets[layer]['pressures'] = self.get_typed_platesets(layer, 'pressure')
            self.platesets[layer]['masses'] = self.get_typed_platesets(layer, 'mass')


    def _generate_switch_map(self) -> None:
        """_summary_

        .. notes:
            - switch_map example,
            ```python
            self.switch_map = {
                'layer_1': {
                    'switch_key_1': {
                        'switch_set_index_1': bool_1, # bool
                        'switch_set_index_2': bool_2, # bool
                        # ...
                    },
                    # ...
                },
                # ...
            }
            ```
        """
        self.switch_map = {}
        for layer in self.layers:
            switches =  self.get_typed_platesets(layer, 'pressure') + \
                self.get_typed_platesets(layer, 'container') + \
                self.get_typed_platesets(layer, 'gate')
            switch_indices = [ switch['index'] for switch in switches]
            self.switch_map[layer] = {
                switch['key']: {
                    index: False for index in switch_indices
                } for switch in switches
            }
            # switch_map ={
            #   'layer_1': {
            #       'switch_key': {
            #           'switch_set_index': bool,
            #           'switch_set_index': bool,
            #           # ...
            #       }
            #   }
            # }
                
        pass


    def _init_dynamic_state(self, state_ao: state.State) -> None:
        """
        Initialize the state for dynamic in-game elements, i.e. elements that move and are interactable.
        """
        log.debug(f'Initalizing dynamic world state...', 'World._init_dynamic_state')
        dynamic_conf = state_ao.get_state('dynamic')
        self.hero = dynamic_conf['hero']
        self.layer = dynamic_conf['hero']['layer']
        self.plot = dynamic_conf['hero']['plot']
        self.npcs = dynamic_conf.get('npcs') if dynamic_conf.get('npcs') is not None else {}
        self.villains = dynamic_conf.get('villains') if dynamic_conf.get('villains') is not None else {}


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


    def _update_sprites(self) -> None:
        """
        Maps npc state to in-game action, applies action and then iterates npc state frame.

        .. notes:
            - This method is essentially an interface between the sprite state and the game world. It determines what happens to a sprite once it is in a state. It has nothing to say about how to came to be in that state, and only what happens when it is there.
        """
        for spriteset_key in ['npcs', 'villains']:
            if spriteset_key == 'npcs':
                iter_set = self.npcs
            elif spriteset_key == 'villains':
                iter_set = self.villains

            for sprite_key, sprite in iter_set.items():
                sprite_props = self.sprite_property_conf[sprite_key]

                if sprite['state'] not in self.sprite_property_conf[sprite_key]['blocking_states']:
                    if 'run' in sprite['state']:
                        speed = sprite_props['run']
                    else:
                        speed = sprite_props['walk']

                    if sprite['state'] == 'walk_up':
                        sprite['position']['y'] -= speed
                    elif sprite['state'] == 'walk_left':
                        sprite['position']['x'] -= speed
                    elif sprite['state'] == 'walk_right':
                        sprite['position']['x'] += speed
                    elif sprite['state'] == 'walk_down':
                        sprite['position']['y'] += speed

                sprite['frame'] += 1

                if self.iterations % sprite_props['poll'] == 0:
                    
                    sprite_pos = (sprite['position']['x'], sprite['position']['y'])
                    intents = self.get_sprite_intent(sprite_key)
                    
                    for intent in intents:
                        if intent['intent'] not in list(self.sprite_property_conf[sprite_key]['paths'].keys()):
                            # if intent is sprite location based

                            log.debug(f'Checking {sprite_key} plot {self.plot} {intent["intent"]} intent conditions...', 'World.update_sprites')
                            intent_pos = paths.locate_intent(
                                intent['intent'], 
                                self.hero, 
                                self.npcs, 
                                self.villains, 
                                self.sprite_property_conf[sprite_key]['paths']
                            )
                            distance = calculator.distance(intent_pos, sprite_pos)

                            if distance <= sprite_props['radii']['aware'] \
                                and sprite['path']['current'] != intent['intent']:
                                
                                log.debug(f'Applying {sprite_key} {intent["intent"]} intent at {intent_pos}...', 'World._update_sprites')
                                sprite['path']['previous'] = sprite['path']['current']
                                sprite['path']['current'] = intent['intent']

                            elif distance >= sprite_props['radii']['aware'] \
                                and sprite['path']['current'] == intent['intent']:

                                log.debug(f'Resetting {sprite_key} memory to {sprite["path"]["previous"]}', 'World.update_sprites')
                                sprite['path']['current'] = sprite['path']['previous']
                                sprite['path']['previous'] = intent['intent']
                        
                    self._reorient(spriteset_key, sprite_key)


                if sprite['frame'] >= self.sprite_state_conf[sprite_key][sprite['state']]['frames']:
                    sprite['frame'] = 0


    def _reorient(self, spriteset_key: str, sprite_key: str) -> None:

        if spriteset_key == 'npcs':
            sprite = self.npcs[sprite_key]
        elif spriteset_key == 'villains':
            sprite = self.villains[sprite_key]
        sprite_hitbox = self.get_sprite_hitbox(spriteset_key, 'strut', sprite_key)

        collision_sets = self.get_collision_sets_relative_to(sprite, sprite_key, 'strut')
        
        pathset = paths.concat_dynamic_paths(
            sprite, 
            self.sprite_property_conf[sprite_key]['paths'], 
            self.hero, 
            self.npcs, 
            self.villains
        )

        paths.reorient(
            sprite,
            sprite_hitbox,
            collision_sets, 
            pathset[sprite['path']['current']],
            self.sprite_property_conf[sprite_key]['collide'],
            self.dimensions
        )


    def _apply_physics(self) -> None:
        """
        
        .. notes:
            - Keep in mind, the sprite collision doesn't care what sprite or strut with which the sprite collided, only what direction the sprite was travelling when the collision happened. The door hit detection, however, _is_ aware of what door with which the player is colliding, in order to locate the world layer to which the door is connected.
            - Technically, there is overlap here. Since sprite is checked against every other sprite for collisions, there are Pn = n!/(n-2)! permutations, but Cn = n!/(2!(n-2)!) distinct combinations. Therefore, Pn - Cn checks are unneccesary. To circumvent this problem (sort of), a collision map is kept internally within this method to keep track of which sprite-to-sprite collisions have already taken place. However, whether or not this is worth the effort, since the map has to be traversed when it is initialized, is an open question? 
            - There is an inherent ordering here affecting how collisions work. Because the NPC set is checked first, the act of an NPC-villain collision will always proceed relative to the NPC, meaning the NPC will recoil and reorient their direction based on the collision, while the villain iteration will miss the collision since the NPC has already been recoiled when the villain's collision detection is attempt.
        .. todos:
            - see third note. It may be possible to use the collision map to also apply the collision to the villain next iteration.
        """

        collision_map = collisions.generate_collision_map(self.npcs, self.villains)

        for spriteset_key in ['hero', 'npcs', 'villains']:
            for sprite_key, sprite in self.get_spriteset(spriteset_key).items():

                # sprite collision detection
                if spriteset_key in ['npcs', 'villains']:
                    for hitbox_key in ['sprite', 'strut']:

                        exclusions = [ sprite_key ]
                        for key, val in collision_map[sprite_key].items():
                            if val:
                                exclusions.append(key)

                        sprite_hitbox = self.get_sprite_hitbox(spriteset_key, hitbox_key, sprite_key)

                        collision_sets = self.get_collision_sets_relative_to(sprite, sprite_key, hitbox_key)

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
                            if sprite['path']['current'] in list(self.sprite_property_conf.keys()):
                                pathset = paths.concat_dynamic_paths(
                                    sprite,
                                    self.sprite_property_conf[sprite_key]['paths'],
                                    self.hero,
                                    self.npcs,
                                    self.villains
                                )
                            else:
                                pathset = self.sprite_property_conf[sprite_key]['paths']

                            paths.reorient(
                                sprite,
                                sprite_hitbox,
                                collision_sets, 
                                pathset[sprite['path']['current']],
                                self.sprite_property_conf[sprite_key]['collide'],
                                self.dimensions
                            )

                        for key, val in collision_map.copy().items():
                            if key not in exclusions and key == sprite_key:
                                for nest_key in val.keys():
                                    collision_map[key][nest_key] = True
                                    collision_map[nest_key][key] = True
    
                # hero collision detection
                elif spriteset_key == 'hero':
                    sprite_hitbox = self.get_sprite_hitbox(spriteset_key, 'sprite', sprite_key)
                    collision_sets = self.get_collision_sets_relative_to(self.hero, 'hero', 'sprite')

                    log.infinite('Checking "hero" for collisions...', '_apply_physics')

                    for collision_set in collision_sets:
                        if collisions.detect_collision(sprite_hitbox, collision_set):
                            collisions.recoil_sprite(sprite, self.sprite_property_conf[sprite_key])

                # mass plate collision detection
                masses = self.platesets[self.layer]['masses'].copy()
                hero_flag = spriteset_key == 'hero'
                for mass in masses:
                    if collisions.detect_collision(mass['hitbox'], [sprite_hitbox]):
                        plate = self.get_plate(self.layer, mass['key'], mass['index'])
                        collisions.recoil_plate(
                            plate, sprite, 
                            self.sprite_property_conf[sprite_key],
                            hero_flag
                        )
                        plate['hitbox'] = collisions.calculate_set_hitbox(
                            self.plate_property_conf[mass['key']]['hitbox'],
                            plate,
                            self.tile_dimensions
                        )
                        self.platesets[self.layer]['masses'] = self.get_typed_platesets(
                            self.layer, 
                            'mass'
                        )

        # TODO: plate-to-plate collisions, plate-to-strut collisions


    def _apply_interaction(self, user_input: dict):
        """_summary_

        :param user_input: _description_
        :type user_input: dict

        .. notes:
            - Collisions with containers are based on their calculated hitboxes, whereas interactions with containers are based on their actual dimensions.
        """
        if user_input['interact']:
            hero_hitbox = self.get_sprite_hitbox('hero', 'sprite', 'hero')

            triggered = False
            for door in self.platesets[self.layer]['doors']:
                if collisions.detect_collision(
                    hero_hitbox,
                    [ door['hitbox'] ]
                ):
                    self.layer = door['content']
                    self.hero['layer'] = door['content']
                    triggered = True
                    break

            if not triggered:
                for container in self.platesets[self.layer]['containers']:
                    key, index = container['key'], container['index']
                    modified_hitbox = (
                        container['position']['x'], 
                        container['position']['y'],
                        self.plate_property_conf[key]['size']['w'],
                        self.plate_property_conf[key]['size']['h']    
                    )
                    if not self.switch_map[self.layer][key][index] and \
                        collisions.detect_collision(
                            hero_hitbox,
                            [ modified_hitbox ]
                        ):
                        self.switch_map[self.layer][key][index] = True
                        triggered = True
                        # TODO: deliver item to hero via content
                        break
                    
            # TODO: gate and pressure interaction implementation


    def _apply_combat(self):
        pass


    def get_strut_hitboxes(self, layer):
        strut_hitboxes = []
        for strut_conf in self.get_strutsets(layer).values():
            sets = strut_conf['sets']
            for strut in sets:
                strut_hitboxes.append(strut['hitbox'])
        return strut_hitboxes


    def get_sprite_hitbox(self, spriteset_key, hitbox_key, sprite_key):
        """
        .. notes:
            - A sprite's hitbox dimensions are fixed, but the actual hitbox coordinates depend on the position of the sprite. This method must be called each iteration of the world loop, so the newest coordinates of the hitbox are retrieved.
        """
        if spriteset_key == 'hero':
            sprite = self.hero
        elif spriteset_key == 'npcs':
            sprite = self.npcs.get(sprite_key)
        elif spriteset_key == 'villains':
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


    def get_sprite_hitboxes(self, spriteset_key, hitbox_key, layer, exclude = None):
        calculated = []

        if spriteset_key == 'npcs':
            iter_set = self.get_npcs(layer)
        elif spriteset_key == 'villains':
            iter_set = self.get_villains(layer)
        else:
            iter_set = {}

        for sprite_key in iter_set.keys():
            if exclude is None or sprite_key not in exclude:
                if spriteset_key == 'npcs':
                    calculated.append(self.get_sprite_hitbox('npcs', hitbox_key, sprite_key))
                elif spriteset_key == 'villains':
                    calculated.append(self.get_sprite_hitbox('villains', hitbox_key, sprite_key))
        return calculated


    def get_sprite_intent(self, sprite_key):
        if sprite_key != 'hero':
            return list(filter(lambda x: x['plot'] == self.plot, self.sprite_property_conf[sprite_key]['intents']))
        return None


    def get_collision_sets_relative_to(self, sprite, sprite_key, hitbox_key):
        vil_hitboxes = self.get_sprite_hitboxes('villains', hitbox_key, sprite['layer'], [sprite_key])
        npc_hitboxes = self.get_sprite_hitboxes('npcs', hitbox_key, sprite['layer'], [sprite_key])

        collision_sets = []
        if npc_hitboxes is not None:
            collision_sets.append(npc_hitboxes)
        if vil_hitboxes is not None:
            collision_sets.append(vil_hitboxes)
        if (hitbox_key =='strut' or sprite_key == 'hero' ) \
             and self.strutsets[sprite['layer']]['hitboxes'] is not None:
            collision_sets.append(self.strutsets[sprite['layer']]['hitboxes'])
        if (hitbox_key =='strut' or sprite_key == 'hero' ) \
             and self.platesets[sprite['layer']]['containers'] is not None:
             collision_sets.append([
                 container['hitbox']
                 for container in self.platesets[sprite['layer']]['containers']
             ])
        return collision_sets


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
            if key not in ['doors', 'containers', 'pressures', 'masses']
        }


    def get_typed_platesets(self, layer, plateset_type):
        typed_platesets = []
        for plate_key, plate_conf in self.get_platesets(layer).items():
            if self.plate_property_conf[plate_key]['type'] == plateset_type:
                for i, plate in enumerate(plate_conf['sets']):
                    typed_platesets.append({
                        'key': plate_key,
                        'index': i,
                        'hitbox': plate['hitbox'],
                        'content': plate['content'],
                        'position': plate['start']
                    })
        return typed_platesets


    def get_plate(self, layer, plate_key, index):
        return self.platesets[layer][plate_key]['sets'][index]


    def get_spriteset(self, spriteset_key):
        if spriteset_key == 'hero':
            return { 'hero': self.hero }
        elif spriteset_key == 'npcs':
            return self.npcs
        elif spriteset_key == 'villains':
            return self.villains
        return None

    def get_formsets(self, formset_key):
        if formset_key in ['tile', 'tiles']:
            return self.tilesets
        elif formset_key in ['strut', 'struts']:
            return self.strutsets
        elif formset_key in ['plate', 'plates']:
            return self.platesets


    def get_sprite(self, sprite_key):
        if sprite_key == 'hero':
            return self.hero
        elif sprite_key in list(self.npcs.keys()):
            return self.npcs[sprite_key]
        elif sprite_key in list(self.villains.keys()):
            return self.villains[sprite_key]
        return None


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
        self.hero['plot'] = self.plot
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

        self._update_sprites()
        self._update_hero(user_input)
        self._apply_physics()
        self._apply_combat()
        self._apply_interaction(user_input)
        self.iterations += 1