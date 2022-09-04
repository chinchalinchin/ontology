import munch
from typing import Union

from onta.actuality \
    import state, conf
from onta.concretion \
    import collisions, composition
from onta.concretion.dasein \
    import abstract, interpret, impulse
from onta.concretion.facticity \
    import gauge, paths
from onta.concretion.noumena \
    import substrata
from onta.metaphysics \
    import settings, logger

log = logger.Logger(
    'onta.world', 
    settings.LOG_LEVEL
)

PLATE_META = [
    'doors',
    'containers',
    'pressures',
    'masses'
]
STRUT_META = [
    'hitboxes'
]

FORM_TYPES = [
    'tiles',
    'struts',
    'plates'
]
ENTITY_TYPES = [
    'sprites'
]


class World():
    # TODO: be careful with closures. 
    
    ## See /docs/DATA_STRUCTURES.md for more information on 
    ##  the following fields.

    # CONFIGURATION FIELDS
    composite_conf = munch.Munch({})
    sprite_stature = munch.Munch({})
    apparel_properties = munch.Munch({})
    plate_properties = munch.Munch({})
    strut_properties = munch.Munch({})
    sprite_properties = munch.Munch({})
    projectile_properties = munch.Munch({})
        # TODO:
        # composite = munch.Munch({})
        # stature = munch.Munch({})
        # properties = munch.Munch({})

    # STATE FIELDS
    tilesets = munch.Munch({})
    strutsets = munch.Munch({})
    platesets = munch.Munch({})
    compositions = munch.Munch({})
    hero = munch.Munch({})
    npcs = munch.Munch({})
    switch_map = munch.Munch({})
    layer = None
    layers = []
    projectiles = []
    # META FIELDS
    dimensions = None
    tile_dimensions = None
    sprite_dimensions = None
    world_bounds = None
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
        log.debug(
            'Initializing world configuration...', 
            'World._init_conf'
        )
        sprite_conf = config.load_sprite_configuration()
        self.sprite_stature, self.sprite_properties, _, self.sprite_dimensions = \
            sprite_conf
        self.apparel_properties = config.load_apparel_configuration()
        self.projectile_properties, _ = config.load_projectile_configuration()
        self.plate_properties, _ = config.load_plate_configuration()
        self.strut_properties, _ = config.load_strut_configuration()
        self.composite_conf = config.load_composite_configuration()
        _, tile_conf = config.load_tile_configuration()
        self.tile_dimensions = (
            tile_conf.tile.w, 
            tile_conf.tile.h
        )


    def _init_static_state(
        self,
        state_ao: state.State
    ) -> None:
        """
        Initialize the state for static in-game elements, i.e. elements that do not move and are not interactable.
        """
        log.debug(
            f'Initializing simple static world state...', 
            'World._init_static_state'
        )
        static_conf = state_ao.get_state('static')

        self.dimensions = gauge.scale(
            (
                static_conf.world.size.w, 
                static_conf.world.size.h
            ),
            self.tile_dimensions,
            static_conf.world.size.units
        )

        for layer_key, layer_conf in static_conf.layers.items():
            self.layers.append(layer_key)

            for asset_type, asset_set in zip(
                [ 'tiles', 'struts', 'plates', 'compositions' ],
                [self.tilesets, self.strutsets, self.platesets, self.compositions]
            ):
                setattr(asset_set, layer_key, layer_conf.get(asset_type))

        self.tilesets, self.strutsets, self.platesets = \
            composition.decompose_compositions(
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
        log.debug(
            f'Calculating stationary hitbox locations...',
            '_generate_stationary_hitboxes'
        )
        self.world_bounds = [
            ( 0, 0, self.dimensions[0], 1 ),
            ( 0, 0, 1, self.dimensions[1] ),
            ( self.dimensions[0], 0, 1, self.dimensions[1] ),
            ( 0, self.dimensions[1], self.dimensions[0], 1 )
        ]
        strut_dicts = munch.unmunchify(self.strutsets)
        plate_dicts = munch.unmunchify(self.platesets)

        strut_prop_dict = munch.unmunchify(self.strut_properties)
        plate_prop_dict = munch.unmunchify(self.plate_properties)

        strut_dicts, plate_dicts = substrata.stationary_hitboxes(
            self.layers,
            self.tile_dimensions,
            strut_dicts,
            plate_dicts,
            strut_prop_dict,
            plate_prop_dict
        )

        self.platesets = munch.munchify(plate_dicts)
        self.strutsets = munch.munchify(strut_dicts)

        for layer in self.layers:
            self.strutsets.get(layer).hitboxes = substrata.strut_hitboxes(
                strut_dicts.get(layer)
            ) + self.world_bounds
            self.platesets.get(layer).doors = self.get_typed_platesets(
                layer, 
                'door'
            )
            self.platesets.get(layer).containers = self.get_typed_platesets(
                layer, 
                'container'
            )
            self.platesets.get(layer).pressures = self.get_typed_platesets(
                layer,  
                'pressure'
            )
            self.platesets.get(layer).masses = self.get_typed_platesets(
                layer,  
                'mass'
            )



    def _generate_switch_map(
        self
    ) -> None:
        for layer in self.layers:
            switches = self.get_typed_platesets(layer, 'pressure') + \
                self.get_typed_platesets(layer, 'container') + \
                self.get_typed_platesets(layer,  'gate')
            switch_indices = [switch.index for switch in switches]
            setattr(
                self.switch_map,
                layer,
                munch.munchify({
                    switch.key: {
                        str(index): False for index in switch_indices
                    } for switch in switches
                })
            )


    def _init_dynamic_state(
        self,
        state_ao: state.State
    ) -> None:
        """
        Initialize the state for dynamic in-game elements, i.e. elements that move and are interactable.
        """
        log.debug(f'Initalizing dynamic world state...',
                  '_init_dynamic_state')
        dynamic_state = state_ao.get_state('dynamic')
        self.hero = dynamic_state.hero
        self.layer = dynamic_state.hero.layer
        self.plot = dynamic_state.hero.plot
        self.npcs = dynamic_state.get('npcs') \
            if dynamic_state.get('npcs') is not None \
            else munch.Munch({})


    def _ruminate(
        self,
        user_input: munch.Munch
    ):
        """Create the _Sprite Intent_\s based on user input in the case of the player _Sprite and _Desires_ in the case of non-playable characters (_NPCs_) .

        :param user_input: _description_
        :type user_input: munch.Munch
        """
        self.hero.intent = interpret.map_input_to_intent(
            self.hero,
            self.sprite_stature,
            user_input
        )

        for sprite_key, sprite in self.npcs.items():
            sprite_props = self.sprite_properties.get(sprite_key)
            sprite_desires = self._sprite_desires(sprite)

            # TODO: order desires?

            if sprite.intent:
                continue

            first_octave = self.iterations % sprite_props.poll.enter == 0
            second_octave = self.iterations % sprite_props.poll.exit == 0

            for sprite_desire in sprite_desires:

                if sprite_desire.plot != self.plot:
                    continue

                instruction = None

                # update delayed desires
                if first_octave:
                    log.infinite(
                        f'Polling {sprite_key}\'s first octave {sprite_desire.mode} desire conditions...',
                        '_ruminate'
                    )

                    if sprite_desire.mode == 'approach':
                        instruction = abstract.approach(
                           sprite_key,
                           sprite,
                           sprite_desire,
                           self.sprite_stature,
                           self.sprite_properties.get(sprite_key),
                           self.get_sprites(),
                           self._reorient
                        )

                    elif sprite_desire.mode == 'engage':
                        instruction = abstract.engage(
                            sprite_key,
                            sprite,
                            sprite_desire,
                            self.sprite_stature,
                            self.sprite_properties.get(sprite_key),
                            self.get_sprites()
                        )

                    elif sprite_desire.mode == 'flee':
                        instruction = abstract.attempt_unflee(
                            sprite_key,
                            sprite,
                            sprite_props,
                            self.get_sprites(),
                            self._reorient
                        )
                    
                # update immediate desires
                elif second_octave:
                    log.infinite(
                        f'Polling {sprite_key}\'s second octave {sprite_desire.mode} desire conditions...',
                        '_ruminate'
                    )

                    if sprite_desire.mode == 'approach':
                        instruction = abstract.attempt_unapproach(
                            sprite_key,
                            sprite,
                            sprite_props,
                            sprite_desire,
                            self.get_sprites()
                        )
                    elif sprite_desire.mode == 'flee':
                        instruction = abstract.flee(
                            sprite_key,
                            sprite,
                            sprite_desire,
                            self._reorient
                        )
                    elif sprite_desire.mode == 'engage':
                        instruction = abstract.attempt_unengage(
                            sprite_key,
                            sprite,
                            sprite_props,
                            sprite_desire,
                            self.get_sprites()
                        )

                if not instruction or instruction == 'continue':
                    continue
                if instruction == 'break':
                    break
                        
            # ensure sprite has intent for next iteration
            # abstract.remember(sprite_key, sprite)


    def _intend(
        self
    ):
        """Transmit _Sprite Intent_ to the _Sprite_ stature and then consume _Intent_

        .. note::
            A _Sprite Intent_ is an in-game data structure used to transmit _Sprite_ stature changes to the _World_ state. If the _Sprite_ represents the player, the _Intent_ was formed from user input. If the _Sprite_ represents a non-playable character (NPC), the _Intent_ was formed from _Sprite Desires_. See documentation for more information.

            ```python
            sprite.intent = munch.Munch({
                'intention': intention, # str
                'action': action, # str
                'direction': direction, # str
                'expression': expression, #
            })
        """
        # what about attention?
        
        for sprite_key, sprite in self.get_sprites().items():
            if not sprite.intent or \
                    sprite.stature.action in self.sprite_stature.decomposition.blocking:
                # NOTE: sprites intents will be altered by impulse module
                # NOTE: if sprite in blocking stature, no intent is transmitted or consumed
                continue

            log.infinite(
                f'Applying intent {sprite.intent.intention} to {sprite_key}\'s stature: {sprite.stature.intention}',
                '_intend'
            )

            # null intentions allowed
            if sprite.intent.intention != sprite.stature.intention:
                log.verbose(f'Switching {sprite_key} intention from {sprite.stature.intention} to {sprite.intent.intention}',
                            '_intend')
                sprite.stature.intention = sprite.intent.intention

            if sprite.intent.get('action') and \
                    sprite.intent.action != sprite.stature.action:
                sprite.frame = 0
                sprite.stature.action = sprite.intent.action

            if sprite.intent.get('direction') and \
                    sprite.intent.direction != sprite.stature.direction:
                sprite.stature.direction = sprite.intent.direction
            
            if sprite.intent.get('attention') and \
                    sprite.intent.attention != sprite.stature.attention:
                sprite.stature.attention = sprite.intent.attention

            if sprite.intent.get('disposition') and \
                    sprite.intent.disposition != sprite.stature.disposition:
                sprite.stature.disposition = sprite.intent.disposition

            # null expresions allowed
            if sprite.intent.expression != sprite.stature.expression:
                sprite.stature.expression = sprite.intent.expression

            log.infinite(f'{sprite_key} stature post intent application: {sprite.stature.intention}',
                         '_intend'
                         )
            sprite.intent = None


    def _act(
        self
    ):
        for sprite_key, sprite in self.get_sprites().items():
            animate = False

            if sprite.stature.intention == 'move':
                impulse.move(
                    sprite,
                    self.sprite_properties.get(sprite_key)
                )
                animate = True

            elif sprite.stature.intention == 'combat':
                impulse.combat(
                    sprite_key,
                    sprite,
                    self.sprite_stature,
                    self.sprite_properties,
                    self.sprite_dimensions,
                    self.apparel_properties,
                    self.projectiles,
                    self.projectile_properties,
                    self.get_sprites()
                )
                animate = True

            elif sprite.stature.intention == 'defend':
                pass

            # reorient sets an intention with an expression, therefore
            #       does an 'express' intention make sense?
            elif sprite.stature.intention == 'express':
                impulse.express(
                    sprite,
                    self.sprite_properties.get(sprite_key)
                )

            elif sprite.stature.intention == 'operate':
                # well, what differentiates using and interacting then?
                impulse.operate(
                    sprite,
                    self.sprite_properties.get(sprite_key),
                    self.platesets.get(sprite.layer),
                    self.plate_properties,
                    self.switch_map
                )
                sprite.stature.intention = None

                # NOTE: operating can change the hero's layer...
                if sprite_key == 'hero' and self.hero.layer != self.layer:
                    self.layer = self.hero.layer

            if animate:
                sprite.frame += 1

                # construct sprite stature string
                sprite_stature_key = composition.compose_animate_stature(
                    sprite, self.sprite_stature
                )
                if sprite.frame >= self.sprite_stature.animate_map.get(sprite_stature_key).frames:
                    sprite.frame = 0
                    if sprite.stature.action in self.sprite_stature.decomposition.blocking:
                        sprite.stature.intention = None
                        # have to set the action to a non-blocking action
                        sprite.stature.action = 'walk'


    def _reorient(
        self,
        sprite_key: str,
        target_key: str,
    ) -> None:

        sprite = self.npcs.get(sprite_key)
        sprite_hitbox = substrata.sprite_hitbox(
            munch.unmunchify(sprite),
            'strut',
            munch.unmunchify(
                self.sprite_properties.get(sprite_key)
            )
        )
        collision_set = collisions.collision_set_relative_to(
            'strut',
            None,
            self.strutsets.get(sprite.layer).hitboxes,
            self.platesets.get(sprite.layer).containers,
            self.get_typed_platesets(
                sprite.layer, 
                'gate'
            ),
            self.switch_map.get(sprite.layer)
        )
        goal = impulse.locate_desire(
            target_key,
            sprite,
            self.get_sprites(),
        )

        log.verbose(
            f'Reorienting {sprite_key} to {goal}', 
            '_reorient'
        )

        return paths.reorient(
            sprite_hitbox,
            collision_set,
            goal,
            self.sprite_properties.get(sprite_key).speed.collide,
            self.dimensions,
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

        collision_map = collisions.generate_collision_map(
            self.get_sprites()
        )

        # SPRITE-TO-SPRITE, SPRITE-TO-STRUT COLLISIONS
        for sprite_key, sprite in self.get_sprites().items():
            for hitbox_key in ['strut', 'sprite']:
                exclusions = [ sprite_key ]
                if hitbox_key == 'sprite':
                    exclusions += [
                        key 
                        for key, val 
                        in collision_map.get(sprite_key).items() 
                        if val
                    ]

                sprite_hitbox = substrata.sprite_hitbox(
                    munch.unmunchify(sprite),
                    hitbox_key,
                    munch.unmunchify(
                        self.sprite_properties.get(sprite_key)
                    )
                )

                if sprite_hitbox is None:
                    continue

                other_sprite_hitboxes = substrata.sprite_hitboxes(
                    munch.unmunchify(
                        self.get_sprites(sprite.layer)
                    ), # can use read-only here since just calculating
                    munch.unmunchify(self.sprite_properties),
                    hitbox_key,
                    exclusions
                )
                    # collisions_set will exclude struts and plates when 
                    # hitbox_key == 'sprite' and exclude sprites when 
                    # hitbox_key == 'strut'
                collision_set = collisions.collision_set_relative_to(
                    hitbox_key,
                    other_sprite_hitboxes,
                    self.strutsets.get(sprite.layer).hitboxes,
                    self.platesets.get(sprite.layer).containers,
                    self.get_typed_platesets(
                        sprite.layer, 
                        'gate'
                    ),
                    self.switch_map.get(sprite.layer)
                )

                log.infinite(
                    f'Checking {sprite_key} for {hitbox_key} collisions...',
                    '_physics'
                )

                collision_box = collisions.detect_collision(
                    sprite_hitbox, 
                    collision_set
                )
                

                if collision_box:
                    log.debug(
                        f'{sprite_key} collision at ({round(sprite.position.x)}, {round(sprite.position.y)})',
                        '_physics'
                    )
                    collisions.recoil_sprite(
                        sprite, 
                        self.sprite_dimensions,
                        self.sprite_properties.get(sprite_key).speed.collide,
                        collision_box
                    )
                    if sprite_key != "hero":
                        sprite_hitbox = substrata.sprite_hitbox(
                            munch.unmunchify(sprite),
                            hitbox_key,
                            munch.unmunchify(
                                self.sprite_properties.get(sprite_key)
                            )
                        )
                        path = impulse.locate_desire(
                            sprite.stature.attention,
                            sprite,
                            self.get_sprites(),
                        )
                        log.debug(
                            f'Reorienting {sprite_key} with path {sprite.stature.attention}',
                            '_physics'
                        )
                        new_direction = paths.reorient(
                            sprite_hitbox,
                            collision_set,
                            path,
                            self.sprite_properties.get(sprite_key).speed.collide,
                            self.dimensions
                        )
                        setattr(
                            sprite,
                            'intent',
                            munch.Munch({
                                'intention': 'move',
                                'action': sprite.stature.action,
                                'direction': new_direction,
                                'expression': sprite.stature.expression,
                                'attention': sprite.stature.attention,
                                'disposition': sprite.stature.disposition
                            })
                        )

                if hitbox_key == 'sprite':
                    for key, val in collision_map.copy().items():
                        if key not in exclusions and \
                                key == sprite_key:
                            for nest_key in val.keys():
                                setattr(
                                    collision_map.get(key), 
                                    nest_key, 
                                    True
                                )
                                setattr(
                                    collision_map.get(nest_key), 
                                    key, 
                                    True
                                )

            # mass collision detection
            collisions.detect_layer_sprite_to_mass_collision(
                sprite,
                self.sprite_properties.get(sprite_key),
                self.platesets,
                self.plate_properties,
                self.tile_dimensions
            )
            # recalculate plate meta after alteration
            self.platesets.get(sprite.layer).masses = self.get_typed_platesets(
                sprite.layer,
                'mass'
            )

        # MASS-TO-PLATE COLLISIONS
        for layer in self.layers:
            mass_hitboxes = [ 
                mass.hitbox.strut 
                for mass in self.platesets.get(layer).masses 
            ]
            pressures = self.platesets.get(layer).pressures

            if not (mass_hitboxes and pressures):
                continue

            collisions.detect_layer_pressure(
                mass_hitboxes,
                pressures,
                self.switch_map.get(layer),
                self.get_gates()
            )
    

        # PROJECTILE-TO-SPRITE, PROJECTILE-TO-STRUT COLLISIONS
        removals = []
        for i, projectile in enumerate(self.projectiles):
            collisions.project(projectile)

            if gauge.distance(
                projectile.current, 
                projectile.origin
            ) > projectile.distance:
                removals.append(i)
                continue

            for target_key, target in self.get_sprites().items():
                if projectile.layer == target.layer:
                    continue

                target_hitbox = substrata.sprite_hitbox(
                    munch.unmunchify(target),
                    'attack',
                    munch.unmunchify(
                        self.sprite_properties.get(target_key)
                    )
                )
                collision_box = collisions.detect_collision(
                    projectile.attackbox,
                    [ target_hitbox ]
                )
                if collision_box:
                    log.debug(
                        f'{projectile.key} struck true on {target_key}'
                        'World._physics'
                    )

        for removed in removals:
            del self.projectiles[removed]

        # TODO: plate-to-plate collisions, plate-to-strut collisions
            # in order to do mass-to-mass collisions efficiently, will need a collision map
            # like with sprites, but the rub here is the keys are {mass_key}_{mass_index}
            # i.e., collision map? 
            #   layer -> first_mass_key -> first_mass_index
            #         -> second_mass_key -> second_mass_index


    def _sprite_desires(
        self,
        sprite: munch.Munch
    ) -> Union[list, None]:
        """_summary_

        :param sprite: _description_
        :type sprite: munch.Munch
        :return: _description_
        :rtype: Union[list, None]
        """
        return list(
            filter(
                lambda x: x.plot == self.plot, sprite.desires
            )
        )


    def get_formset(
        self,
        formset_key: str
    ) -> munch.Munch:
        """_summary_

        :param formset_key: _description_
        :type formset_key: str
        :return: _description_
        :rtype: dict
        """
        if formset_key in [
            'tile',
            'tiles',
            'tileset',
            'tilesets'
        ]:
            return self.tilesets
        elif formset_key in [
            'strut',
            'struts',
            'strutset',
            'strutsets'
        ]:
            return self.strutsets
        elif formset_key in [
            'plate',
            'plates'
            'plateset',
            'platesets'
        ]:
            return self.platesets


    def get_tilesets(
        self,
        layer: str
    ) -> munch.Munch:
        if self.tilesets.get(layer) is None:
            setattr(self.tilesets, layer, munch.Munch({}))
        return self.tilesets.get(layer)


    def get_strutsets(
        self,
        layer: str
    ) -> munch.Munch:
        """Returns all struts on a given layer of the _World_.

        :param layer: The layer from which to retrieve strutsets.
        :type layer: str
        :return: Munchified strutsets
        :rtype: munch.Munch
        """
        if self.strutsets.get(layer) is None:
            setattr(self.strutsets, layer, munch.Munch({}))
        return munch.munchify({
            key: val
            for key, val in self.strutsets.get(layer).items()
            if key not in STRUT_META
        })


    def get_platesets(
        self,
        layer: str
    ) -> munch.Munch:
        """Returns all plates, regardless of type, on a given layer of the _World_.

        :param layer: The layer from which to retrieve platesets.
        :type layer: str
        :return: Munchified platesets
        :rtype: munch.Munch
        """
        if self.platesets.get(layer) is None:
            setattr(self.platesets, layer, munch.Munch({}))
        return munch.munchify({
            key: val
            for key, val in self.platesets.get(layer).items()
            if key not in PLATE_META
        })


    def get_typed_platesets(
        self,
        layer: str,
        plateset_type: str
    ) -> list:
        """_summary_

        :param layer: The _World_ layer from which to retrieve platesets.
        :type layer: str
        :param plateset_type: The type of plateset to retrieve. Allowable values: `gate`, `pressure`, `mass`, `door`, `container`.
        :type plateset_type: str
        :return: A formatted list of platesets matching the passed in type.
        :rtype: list

        ```python
        typed_plates = [
            {
                'key': key,
                'index': index,
                'hitbox': hitbox
                'content': content,
                'position': position
            }
        ]
        ```
        """
        typed_platesets = []
        for plate_key, plate_conf in self.get_platesets(layer).items():
            if self.plate_properties.get(plate_key).type != plateset_type:
                continue
            typed_platesets += [ 
                munch.Munch({
                    'key': plate_key,
                    'index': i,
                    'hitbox': plate.hitbox,
                    'content': plate.content,
                    'position': plate.start
                }) for i, plate in enumerate(plate_conf.sets)
            ]
        return typed_platesets


    def get_plate(
        self,
        layer: str,
        plate_key: str,
        index: int
    ) -> munch.Munch:
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
        return self.platesets.get(layer).get(plate_key).sets[index]


    def get_gates(
        self
    ) -> list:
        gates = []
        for nested_layer in self.layers:
            gates = gates + self.get_typed_platesets(nested_layer, 'gate')
        return gates


    def get_sprites(
        self,
        layer: str = None
    ) -> munch.Munch:
        """Get all _Sprite_\s.

        :param layer: Filter sprites by given layer, defaults to None
        :type layer: str, optional
        :return: All sprites, or all sprites on a given layer if `layer` is provided.
        :rtype: dict

        .. warning::
            This method creates a copy of `self.npcs` if `layer is not None`. If you modify any attributes on the return value when a `layer` is provided, it will not update the _Sprite_'s corresponding attribute in the world state. In order to alter the _Sprite_ state information, you **cannot** specify the layer. Specifying the `layer` is intended to be a **READ-ONLY** operation, called from the `view.Renderer` class when rendering _Sprite_ positions on screen.
        """
        spriteset = {
            'hero': self.hero
        }
        if layer is None:
            spriteset.update(self.npcs)
        else:
            spriteset.update(self.get_npcs(layer))
        return spriteset


    def get_npcs(
        self,
        layer: str
    ) -> munch.Munch:
        """ This method is **READ-ONLY**.

        :param layer: _description_
        :type layer: str
        :return: _description_
        :rtype: munch.Munch

        .. warning::
            This method creates a copy of `self.npcs`. If you modify any attributes on the return value, it will not update the _Sprite_'s corresponding attribute in the world state.
        """
        return munch.munchify({
            key: val
            for key, val in self.npcs.items()
            if val.layer == layer
        })


    def get_sprite(
        self,
        sprite_key: str
    ) -> munch.Munch:
        if sprite_key == 'hero':
            return self.hero
        elif sprite_key in list(self.npcs.keys()):
            return self.npcs.get(sprite_key)
        return None


    def save(
        self,
        state_ao: state.State
    ) -> None:
        self.hero.layer = self.layer
        self.hero.plot = self.plot
        dynamic_conf = munch.munchify({
            'hero': self.hero,
            'npcs': self.npcs,
        })
        state_ao.save_state('dynamic', dynamic_conf)


    def iterate(
        self,
        user_input: munch.Munch
    ) -> None:
        """Update the _World_ state.

        :param user_input: Map of user input `bool`s
        :type user_input: dict
        """
        self._ruminate(user_input)
        self._intend()
        self._act()
        self._physics()
        self.iterations += 1
