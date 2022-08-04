from typing import Union
import onta.settings as settings
import onta.load.state as state
import onta.load.conf as conf
import onta.util.logger as logger
import onta.engine.calculator as calculator
import onta.engine.collisions as collisions
import onta.engine.paths as paths
import onta.engine.formulae as formulae

log = logger.Logger('onta.world', settings.LOG_LEVEL)

PLATE_META = [
    'doors', 
    'containers', 
    'pressures', 
    'masses'
]
STRUT_META =  [
    'hitboxes'
]

class World():
    """
    """

    # CONFIGURATION FIELDS
    composite_conf = {}
    """
    ```python
    self.composite_conf = {

    }
    ```
    """
    sprite_state_conf = {}
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
    plate_properties = {}
    """
    """
    strut_properties = {}
    """
    Holds strut property configuration information
    ```python
    self.strut_properties = {
            'strut_1': {
                'hitbox_1': hitbox_dim, # tuple
                # ...
            }
        }
    ```
    """
    sprite_properties = {}
    """
    ```python
    self.sprite_properties = {
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
    # FORM SET FIELDS
    tilesets = {}
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
    strutsets = {}
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
    platesets = {}
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
    compositions = {}
    """
    ```python
    self.compositions = {
        'compose_1': {
            'tiles': {
                'tile_1': {
                    'sets': [
                        {
                            'start': {
                                'x': x, # int
                                'y': y, # int
                            },
                            'cover': cover
                        }
                    ]
                },
                # ...
            }
            'struts': {
                'strut_1':{
                    'sets': [
                        {
                            'start': {
                                'x': x, #int
                                'y': y, #int
                            },
                            'cover': cover, # bool
                        }
                    ]
                },
                # ...
            },
            'plates': {
                # ...
            },
        }
    }
    ```
    """
    # SPRITE SET FIELDS
    hero = {}
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
    npcs = {}
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
    # OTHER FIELDS
    dimensions = None
    """
    ```python
    self.dimensions = (w, h) # tuple
    ```
    """
    tile_dimensions = None
    """
    ```python
    self.tile_dimensions = (w, h) # tuple
    ```
    """
    layer = None
    """
    self.layer = 'one' # str
    """
    layers = []
    """
    self.layers = [
        'one', # str
        'two', # str
        # ...
    ]
    """
    switch_map = None
    """
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
    iterations = 0

    def __init__(
        self, 
        ontology_path: str = settings.DEFAULT_DIR
    ) -> None:
        """
        Creates an instance of `onta.world.World` and calls internal methods to initialize in-game element configuration, the game's static state and the game's dynamic state.

        .. note:
            Configuration and state are passed in to populate internal dictionaries. No references are kept to the `config` or `state_ao` objects.
        """
        config = conf.Conf(ontology_path)
        state_ao = state.State(ontology_path)
        self._init_conf(config)
        self._init_static_state(state_ao)
        self._init_dynamic_state(state_ao)


    def _init_conf(
        self, 
        config: conf.Conf
    ) -> None:
        """ 
        Initialize configuration properties for in-game elements in the memory.
        """
        log.debug('Initializing world configuration...', 'World._init_conf')
        sprite_conf = config.load_sprite_configuration()
            # skipping sheet conf and sprite size
            # NOTE: might need sprite size at some point.
        self.sprite_state_conf, self.sprite_properties, _, _= sprite_conf
        self.plate_properties, _ = config.load_plate_configuration()
        self.strut_properties, _ = config.load_strut_configuration()
        self.composite_conf = config.load_composite_configuration()
        tile_conf = config.load_tile_configuration()
        self.tile_dimensions = (
            tile_conf['tile']['w'], 
            tile_conf['tile']['h']
        )


    def _init_static_state(
        self, 
        state_ao: state.State
    ) -> None:
        """
        Initialize the state for static in-game elements, i.e. elements that do not move and are not interactable.
        """
        log.debug(f'Initializing simple static world state...', 'World._init_static_state')
        static_conf = state_ao.get_state('static')

        self.dimensions = calculator.scale(
            (
                static_conf['world']['size']['w'], 
                static_conf['world']['size']['h']
            ),
            self.tile_dimensions,
            static_conf['world']['size']['units']
        )

        for layer_key, layer_conf in static_conf['layers'].items():
            self.layers.append(layer_key)
            self.tilesets[layer_key] = layer_conf.get('tiles')
            self.strutsets[layer_key] = layer_conf.get('struts')
            self.platesets[layer_key] = layer_conf.get('plates')
            self.compositions[layer_key] = layer_conf.get('compositions')

        (
            self.tilesets, 
            self.strutsets, 
            self.platesets
        ) = formulae.decompose_compositions_into_sets(
            self.layers,
            self.compositions,
            self.composite_conf,
            self.tile_dimensions,
            self.tilesets,
            self.strutsets,
            self.platesets
        )

        self._generate_stationary_hitboxes()
        self._generate_switch_map()


    def _generate_stationary_hitboxes(
        self
    ) -> None:
        """
        Construct static hitboxes from object dimensions and properties.

        .. note::
            All of the strut hitboxes are condensed into a list in `self.strutsets['hitboxes']`, so that strut hitboxes only need calculated once.
        """
        log.debug(f'Calculating stationary hitbox locations...', 'World._init_stationary_hitboxes')
        for layer in self.layers:
            for static_set in ['strutset', 'plateset']:

                if static_set == 'strutset':
                    iter_set = self.get_strutsets(layer).copy()
                    props = self.strut_properties
                elif static_set == 'plateset':
                    iter_set = self.get_platesets(layer).copy()
                    props = self.plate_properties
                
                for set_key, set_conf in iter_set.items():
                    log.debug(f'Initializing {static_set} {set_key} hitboxes', 'World._init_hitboxes')

                    for i, set_conf in enumerate(set_conf['sets']):

                        set_hitbox = collisions.calculate_set_hitbox(
                            props[set_key]['hitbox'], 
                            set_conf, 
                            self.tile_dimensions
                        )
                        if static_set == 'strutset' :
                            self.strutsets[layer][set_key]['sets'][i]['hitbox'] = set_hitbox
                        elif static_set == 'plateset':
                            self.platesets[layer][set_key]['sets'][i]['hitbox'] = set_hitbox
            
            # condense all the hitboxes into a list and save to strutsets,
            # to avoid repeated internal calls to `_strut_hitboxes`
            # however, this now means these dictionaries have to have these 
            # keys filtered out if the idea is to iterate through them.
            # therefore, can no longer directly touch these properties, but
            # must access them through get methods.
            world_bounds = [
                (0, 0, self.dimensions[0], 1), 
                (0, 0, 1, self.dimensions[1]),
                (self.dimensions[0], 0, 1, self.dimensions[1]),
                (0, self.dimensions[1], self.dimensions[0], 1)
            ]
            self.strutsets[layer]['hitboxes'] = world_bounds + self._strut_hitboxes(layer)
            self.platesets[layer]['doors'] = self.get_typed_platesets(layer, 'door')
            self.platesets[layer]['containers'] = self.get_typed_platesets(layer, 'container')
            self.platesets[layer]['pressures'] = self.get_typed_platesets(layer, 'pressure')
            self.platesets[layer]['masses'] = self.get_typed_platesets(layer, 'mass')


    def _generate_switch_map(
        self
    ) -> None:
        """_summary_

        .. note::
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


    def _init_dynamic_state(
        self, 
        state_ao: state.State
    ) -> None:
        """
        Initialize the state for dynamic in-game elements, i.e. elements that move and are interactable.
        """
        log.debug(f'Initalizing dynamic world state...', 'World._init_dynamic_state')
        dynamic_state = state_ao.get_state('dynamic')
        self.hero = dynamic_state['hero']
        self.layer = dynamic_state['hero']['layer']
        self.plot = dynamic_state['hero']['plot']
        self.npcs = dynamic_state.get('npcs') if dynamic_state.get('npcs') is not None else {}


    def _update_hero(
        self, 
        user_input: dict
    ) -> None: 
        """
        Map user input to new hero state, apply state action and iterate state frame.
        """
        if self.hero['state'] not in self.sprite_state_conf['blocking_states']:
            if 'run' in self.hero['state']:
                speed = self.sprite_properties['hero']['run']
            else:
                speed = self.sprite_properties['hero']['walk']

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
                if self.hero['state'] != 'walk_left':
                    self.hero['frame'] = 0
                    self.hero['state'] = 'walk_left'

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
                if self.hero['state'] != 'walk_right':
                    self.hero['frame'] = 0
                    self.hero['state'] = 'walk_right'
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

        if self.hero['frame'] >= self.sprite_state_conf['animate_states'][
            self.hero['state']
        ]['frames']:
            self.hero['frame'] = 0


    def _update_sprites(
        self
    ) -> None:
        """
        Maps npc state to in-game action, applies action and then iterates npc state frame.

        .. note::
            This method is essentially an interface between the sprite state and the game world. It determines what happens to a sprite once it is in a state. It has nothing to say about how to came to be in that state, and only what happens when it is there.
        """


        for sprite_key, sprite in self.npcs.items():
            sprite_props = self.sprite_properties[sprite_key]
            sprite_paths = list(self.sprite_properties[sprite_key]['paths'].keys())
            sprite_intents = self._sprite_intent(sprite_key)


            if sprite['state'] not in self.sprite_state_conf['blocking_states']:
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

            if self.iterations % sprite_props['poll'] == 0:
                sprite_pos = (
                    sprite['position']['x'], 
                    sprite['position']['y']
                )
                
                for intent in sprite_intents:
                    if intent['intent'] not in sprite_paths:
                        # if intent is sprite location based

                        log.debug(f'Checking {sprite_key} plot {self.plot} {intent["intent"]} intent conditions...', 
                            'World.update_sprites')
                        intent_pos = paths.locate_intent(
                            intent['intent'], 
                            self.hero, 
                            self.npcs, 
                            self.sprite_properties[sprite_key]['paths']
                        )
                        distance = calculator.distance(intent_pos, sprite_pos)

                        if distance <= sprite_props['radii']['aware'] \
                            and sprite['path']['current'] != intent['intent']:
                            
                            log.debug(f'Applying {sprite_key} {intent["intent"]} intent at {intent_pos}...', 
                                'World._update_sprites')
                            sprite['path']['previous'] = sprite['path']['current']
                            sprite['path']['current'] = intent['intent']

                        elif distance >= sprite_props['radii']['aware'] \
                            and sprite['path']['current'] == intent['intent']:

                            log.debug(f'Resetting {sprite_key} memory to {sprite["path"]["previous"]}', 
                                'World.update_sprites')
                            sprite['path']['current'] = sprite['path']['previous']
                            sprite['path']['previous'] = intent['intent']
                    
                self._reorient(sprite_key)

            if sprite['state'] in self.sprite_state_conf['animate_states']:
                sprite['frame'] += 1
                if sprite['frame'] >= self.sprite_state_conf['animate_states'][
                    sprite['state']
                ]['frames']:
                    sprite['frame'] = 0


    def _reorient(
        self, 
        sprite_key: str
    ) -> None:

        sprite = self.npcs[sprite_key]

        sprite_hitbox = self._sprite_hitbox(
            sprite_key, 
            'strut'
        )

        collision_sets = self._collision_sets_relative_to(
            sprite_key, 
            sprite['layer'], 
            'strut'
        )
        
        pathset = paths.concat_dynamic_paths(
            sprite, 
            self.sprite_properties[sprite_key]['paths'], 
            self.hero, 
            self.npcs, 
        )

        paths.reorient(
            sprite,
            sprite_hitbox,
            collision_sets, 
            pathset[sprite['path']['current']],
            self.sprite_properties[sprite_key]['collide'],
            self.dimensions
        )


    def _physics(
        self
    ) -> None:
        """
        
        .. note::
            Keep in mind, the sprite collision doesn't care what sprite or strut with which the sprite collided, only what direction the sprite was travelling when the collision happened. The door hit detection, however, _is_ aware of what door with which the player is colliding, in order to locate the world layer to which the door is connected.
        .. note::
            Technically, there is overlap here. Since sprite is checked against every other sprite for collisions, there are Pn = n!/(n-2)! permutations, but Cn = n!/(2!(n-2)!) distinct combinations. Therefore, Pn - Cn checks are unneccesary. To circumvent this problem (sort of), a collision map is kept internally within this method to keep track of which sprite-to-sprite collisions have already taken place. However, whether or not this is worth the effort, since the map has to be traversed when it is initialized, is an open question? 
        """

        collision_map = collisions.generate_collision_map(self.npcs)

        for sprite_key, sprite in self.get_sprites().items():

            # hero collision detection
            if sprite_key == 'hero':
                sprite_hitbox = self._sprite_hitbox(
                    sprite_key, 
                    'sprite'
                )
                collision_sets = self._collision_sets_relative_to(
                    'hero', 
                    self.layer,
                    'sprite'
                )

                log.infinite('Checking "hero" for collisions...', '_apply_physics')

                for collision_set in collision_sets:
                    if collisions.detect_collision(
                        sprite_hitbox, 
                        collision_set
                    ):
                        collisions.recoil_sprite(
                            sprite, 
                            self.sprite_properties[sprite_key]
                        )

            # sprite collision detection
            else:
                for hitbox_key in ['sprite', 'strut']:

                    exclusions = [ sprite_key ]
                    for key, val in collision_map[sprite_key].items():
                        if val:
                            exclusions.append(key)

                    sprite_hitbox = self._sprite_hitbox(
                        sprite_key, 
                        hitbox_key
                    )

                    collision_sets = self._collision_sets_relative_to(
                        sprite_key, 
                        sprite['layer'],
                        hitbox_key
                    )

                    log.infinite(f'Checking"{sprite_key}" with hitbox {sprite_hitbox} \
                        for {hitbox_key} collisions...', '_apply_physics')

                    collided = False
                    for collision_set in collision_sets:
                        if collisions.detect_collision(
                            sprite_hitbox, 
                            collision_set
                        ):
                            collided =True
                            collisions.recoil_sprite(
                                sprite, 
                                self.sprite_properties[sprite_key]
                            )
                    if collided:
                            # recalculate hitbox after sprite recoils
                        sprite_hitbox = self._sprite_hitbox(
                            sprite_key, 
                            hitbox_key
                        )
                        # if current path is sprite based...
                        if sprite['path']['current'] in list(self.sprite_properties.keys()):
                            pathset = paths.concat_dynamic_paths(
                                sprite,
                                self.sprite_properties[sprite_key]['paths'],
                                self.hero,
                                self.npcs,
                            )
                        # else just use the static props paths...
                        else:
                            pathset = self.sprite_properties[sprite_key]['paths']

                        paths.reorient(
                            sprite,
                            sprite_hitbox,
                            collision_sets, 
                            pathset[sprite['path']['current']],
                            self.sprite_properties[sprite_key]['collide'],
                            self.dimensions
                        )

                    for key, val in collision_map.copy().items():
                        if key not in exclusions and key == sprite_key:
                            for nest_key in val.keys():
                                collision_map[key][nest_key] = True
                                collision_map[nest_key][key] = True


            # mass plate collision detection
            masses = self.platesets[self.layer]['masses'].copy()
            hero_flag = sprite_key == 'hero'
            for mass in masses:
                if collisions.detect_collision(
                    mass['hitbox'], 
                    [sprite_hitbox]
                ):
                    plate = self.get_plate(self.layer, mass['key'], mass['index'])
                    collisions.recoil_plate(
                        plate, sprite, 
                        self.sprite_properties[sprite_key],
                        hero_flag
                    )
                    plate['hitbox'] = collisions.calculate_set_hitbox(
                        self.plate_properties[mass['key']]['hitbox'],
                        plate,
                        self.tile_dimensions
                    )
                    self.platesets[self.layer]['masses'] = self.get_typed_platesets(
                        self.layer, 
                        'mass'
                    )

        # TODO: plate-to-plate collisions, plate-to-strut collisions


    def _interaction(
        self, 
        user_input: dict
    ) -> None:
        """_summary_

        :param user_input: Dictionary containing the user input keys mapped to their corresponding _directions_ and _actions_, i.e. the result of calling `onta.control.Controller().poll()`
        :type user_input: dict

        .. note::
            Collisions with containers are based on their calculated hitboxes, whereas interactions with containers are based on their actual dimensions.
        """
        if user_input['interact']:
            hero_hitbox = self._sprite_hitbox('hero', 'sprite')

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
                        self.plate_properties[key]['size']['w'],
                        self.plate_properties[key]['size']['h']    
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


    def _combat(
        self
    ) -> None:
        pass


    def _collision_sets_relative_to(
        self, 
        sprite_key: str, 
        layer_key: str, 
        hitbox_key: str
    ) -> list:
        """Returns a list of the typed hitbox a given sprite can possibly collide with on a given layer. 

        :param sprite: _description_
        :type sprite: str
        :param sprite_key: _description_
        :type sprite_key: str
        :param hitbox_key: _description_
        :type hitbox_key: str
        :return: list of lists containing the possible collision hitboxes
        :rtype: list

        .. note::
            This method inherently takes into account a sprite's layer when determining the collision sets it must consider.
        """
        # TODO: I think it would be simpler to return a list (well, it definitely would). would need to unpack each individual list and append 
        # elements. would also need to examine how this method gets invoked and whether it truly would be simpler...
        # if so, change name to _collision_set_relative_to()
        npc_hitboxes = self._sprite_hitboxes(
            hitbox_key, 
            layer_key, 
            [sprite_key]
        )

        collision_sets = []
        if npc_hitboxes is not None:
            collision_sets.append(
                npc_hitboxes
            )

        if (hitbox_key =='strut' or sprite_key == 'hero' ) \
             and self.strutsets[layer_key]['hitboxes'] is not None:
            collision_sets.append(
                self.strutsets[layer_key]['hitboxes']
            )

        if (hitbox_key =='strut' or sprite_key == 'hero' ) \
             and self.platesets[layer_key]['containers'] is not None:
             collision_sets.append(
                [ 
                    container['hitbox']
                    for container in self.platesets[layer_key]['containers']
                ]
            )
        return collision_sets


    def _strut_hitboxes(
        self, 
        layer: str
    ) -> list:
        """_summary_

        :param layer: _description_
        :type layer: str
        :return: _description_
        :rtype: list
        """
        strut_hitboxes = []
        for strut_conf in self.get_strutsets(layer).values():
            sets = strut_conf['sets']
            for strut in sets:
                strut_hitboxes.append(strut['hitbox'])
        return strut_hitboxes


    def _sprite_hitbox(
        self, 
        sprite_key: str, 
        hitbox_key: str
    ) -> Union[tuple, None]:
        """_summary_

        :param sprite_key: _description_
        :type sprite_key: str
        :param hitbox_key: _description_
        :type hitbox_key: str
        :return: _description_
        :rtype: Union[tuple, None]

        .. note::
            A sprite's hitbox dimensions are fixed, but the actual hitbox coordinates depend on the position of the sprite. This method must be called each iteration of the world loop, so the newest coordinates of the hitbox are retrieved.
        """
        sprite = None
        if sprite_key == 'hero':
            sprite = self.hero
        else:
            sprite = self.npcs.get(sprite_key)

        if sprite is not None:
            raw_hitbox = self.sprite_properties[sprite_key]['hitboxes'][hitbox_key]
            calc_hitbox = (
                sprite['position']['x'] + raw_hitbox['offset']['x'],
                sprite['position']['y'] + raw_hitbox['offset']['y'],
                raw_hitbox['size']['w'],
                raw_hitbox['size']['h']
            )
            return calc_hitbox
        return None


    def _sprite_hitboxes(
        self, 
        hitbox_key: str, 
        layer: str, 
        exclude: list = None
    ) -> list:
        """_summary_

        :param hitbox_key: _description_
        :type hitbox_key: str
        :param layer: _description_
        :type layer: str
        :param exclude: _description_, defaults to None
        :type exclude: list, optional
        :return: _description_
        :rtype: list
        """
        calculated = []

        for sprite_key in  self.get_npcs(layer).keys():
            if exclude is None or sprite_key not in exclude:
                calculated.append(self._sprite_hitbox(sprite_key, hitbox_key))
        return calculated


    def _sprite_intent(
        self, 
        sprite_key: str
    ) -> Union[list, None]:
        """_summary_

        :param sprite_key: _description_
        :type sprite_key: str
        :return: _description_
        :rtype: Union[list, None]
        """
        if sprite_key != 'hero':
            return list(
                filter(
                    lambda x: x['plot'] == self.plot, 
                    self.sprite_properties[sprite_key]['intents']
                )
            )
        return None


    def get_formset(
        self, 
        formset_key: str
    ) -> dict:
        """_summary_

        :param formset_key: _description_
        :type formset_key: str
        :return: _description_
        :rtype: dict
        """
        if formset_key in ['tile', 'tiles']:
            return self.tilesets
        elif formset_key in ['strut', 'struts']:
            return self.strutsets
        elif formset_key in ['plate', 'plates']:
            return self.platesets


    def get_tilesets(
        self, 
        layer: str
    ) -> dict:
        return self.tilesets[layer] if self.tilesets[layer] is not None else { }


    def get_strutsets(
        self, 
        layer: str
    ) -> dict:
        iter_set = self.strutsets[layer].items() if self.strutsets[layer] is not None else { }
        return {
            key: val
            for key, val in iter_set
            if key not in STRUT_META
        }
    

    def get_platesets(
        self, 
        layer: str
    ) -> dict:
        iter_set = self.platesets[layer].items() if self.platesets[layer] is not None else { }
        return {
            key: val
            for key, val in iter_set
            if key not in PLATE_META
        }


    def get_typed_platesets(
        self, 
        layer: str, 
        plateset_type: str
    ) -> list:
        """_summary_

        :param layer: _description_
        :type layer: str
        :param plateset_type: _description_
        :type plateset_type: str
        :return: _description_
        :rtype: list
        """
        typed_platesets = []
        for plate_key, plate_conf in self.get_platesets(layer).items():
            if self.plate_properties[plate_key]['type'] != plateset_type:
                continue
            for i, plate in enumerate(plate_conf['sets']):
                typed_platesets.append({
                    'key': plate_key,
                    'index': i,
                    'hitbox': plate['hitbox'],
                    'content': plate['content'],
                    'position': plate['start']
                })
        return typed_platesets


    def get_plate(
        self, 
        layer: str, 
        plate_key: str, 
        index: int
    ) -> dict:
        """_summary_

        :param layer: _description_
        :type layer: str
        :param plate_key: _description_
        :type plate_key: str
        :param index: _description_
        :type index: int
        :return: _description_
        :rtype: dict
        """
        return self.platesets[layer][plate_key]['sets'][index]


    def get_sprites(
        self, 
        layer: str= None
    ) -> dict:
        """Get all _Sprite_\s.

        :param layer: Filter sprites by given layer, defaults to None
        :type layer: str, optional
        :return: All sprites, or all sprites on a given layer if `layer` is provided.
        :rtype: dict
        """
        spriteset = { 'hero': self.hero }
        if layer is None:
            spriteset.update(self.npcs)
        else: 
            spriteset.update(self.get_npcs(layer))
        return spriteset


    def get_npcs(
        self, 
        layer: str
    ) -> dict:
        return {
            key: val
            for key, val 
            in self.npcs.items()
            if val['layer'] == layer
        }


    def get_sprite(
        self, 
        sprite_key: str
    ) -> dict:
        if sprite_key == 'hero':
            return self.hero
        elif sprite_key in list(self.npcs.keys()):
            return self.npcs[sprite_key]
        return None


    def save(
        self, 
        state_ao: state.State
    ) -> None:
        self.hero['layer'] = self.layer
        self.hero['plot'] = self.plot
        dynamic_conf = {
            'hero': self.hero,
            'npcs': self.npcs,
        }
        state_ao.save_state('dynamic', dynamic_conf)


    def iterate(
        self, 
        user_input: dict
    ) -> None:
        """Update the _World_ state.

        :param user_input: Map of user input `bool`s
        :type user_input: dict
        """

        self._update_sprites()
        self._update_hero(user_input)
        self._physics()
        self._combat()
        self._interaction(user_input)
        self.iterations += 1