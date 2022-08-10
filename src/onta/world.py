from typing import Union

import munch


import onta.settings as settings

import onta.loader.state as state
import onta.loader.conf as conf

import onta.engine.collisions as collisions
import onta.engine.instinct.interpret as interpret
import onta.engine.instinct.impulse as impulse
import onta.engine.paths as paths
import onta.engine.static.formulae as formulae
import onta.engine.static.calculator as calculator
import onta.engine.static.logic as logic

import onta.util.logger as logger

log = logger.Logger('onta.world', settings.LOG_LEVEL)

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
    """
    """

    ## See /docs/DATA_STRUCTURES.md for more information on 
    ##  the following fields.
    # CONFIGURATION FIELDS
    composite_conf = munch.Munch({})
    sprite_stature = munch.Munch({})
    apparel_stature = munch.Munch({})
    plate_properties = munch.Munch({})
    strut_properties = munch.Munch({})
    sprite_properties = munch.Munch({})
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
        log.debug('Initializing world configuration...', '_init_conf')
        sprite_conf = config.load_sprite_configuration()
        self.sprite_stature, self.sprite_properties, _, self.sprite_dimensions = sprite_conf
        self.apparel_stature = config.load_apparel_configuration()
        self.plate_properties, _ = config.load_plate_configuration()
        self.strut_properties, _ = config.load_strut_configuration()
        self.composite_conf = config.load_composite_configuration()
        tile_conf = config.load_tile_configuration()
        self.tile_dimensions = (tile_conf.tile.w, tile_conf.tile.h)


    def _init_static_state(
        self,
        state_ao: state.State
    ) -> None:
        """
        Initialize the state for static in-game elements, i.e. elements that do not move and are not interactable.
        """
        log.debug(f'Initializing simple static world state...', '_init_static_state')
        static_conf = state_ao.get_state('static')

        self.dimensions = calculator.scale(
            (static_conf.world.size.w, static_conf.world.size.h),
            self.tile_dimensions,
            static_conf.world.size.units
        )

        for layer_key, layer_conf in static_conf.layers.items():
            self.layers.append(layer_key)

            for asset_type, asset_set in zip(
                ['tiles', 'struts', 'plates', 'compositions'],
                [self.tilesets, self.strutsets, self.platesets, self.compositions]
            ):
                setattr(asset_set, layer_key, layer_conf.get(asset_type))

        self.tilesets, self.strutsets, self.platesets = \
            formulae.decompose_compositions_into_sets(
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
        for layer in self.layers:
            for static_set in ['strutset', 'plateset']:

                if static_set == 'strutset':
                    iter_set = self.get_strutsets(layer).copy()
                    props = self.strut_properties
                elif static_set == 'plateset':
                    iter_set = self.get_platesets(layer).copy()
                    props = self.plate_properties

                for set_key, set_conf in iter_set.items():
                    log.verbose(
                        f'Initializing {static_set} {set_key} hitboxes',
                        '_generate_stationary_hitboxes'
                    )

                    for i, set_conf in enumerate(set_conf.sets):

                        if props.get(set_key).get('type') == 'mass':
                            set_sprite_hitbox = collisions.calculate_set_hitbox(
                                props.get(set_key).hitbox.sprite,
                                set_conf,
                                self.tile_dimensions
                            )
                            set_strut_hitbox = collisions.calculate_set_hitbox(
                                props.get(set_key).hitbox.strut,
                                set_conf,
                                self.tile_dimensions
                            )
                            setattr(
                                self.platesets.get(layer).get(set_key).sets[i],
                                'hitbox',
                                munch.Munch({})
                            )
                            setattr(
                                self.platesets.get(layer).get(set_key).sets[i].hitbox,
                                'sprite',
                                set_sprite_hitbox
                            )
                            setattr(
                                self.platesets.get(layer).get(set_key).sets[i].hitbox,
                                'strut',
                                set_strut_hitbox
                            )
                            continue

                        set_hitbox = collisions.calculate_set_hitbox(
                            props.get(set_key).hitbox,
                            set_conf,
                            self.tile_dimensions
                        )
                        if static_set == 'strutset':
                            setattr(
                                self.strutsets.get(layer).get(set_key).sets[i],
                                'hitbox',
                                set_hitbox
                            )
                            continue
                        setattr(
                            self.platesets.get(layer).get(set_key).sets[i],
                            'hitbox',
                            set_hitbox
                        )

            # TODO : world bounds need to be treated separated
            self.world_bounds = [
                ( 0, 0, self.dimensions[0], 1 ),
                ( 0, 0, 1, self.dimensions[1] ),
                ( self.dimensions[0], 0, 1, self.dimensions[1] ),
                ( 0, self.dimensions[1], self.dimensions[0], 1 )
            ]

            self.strutsets.get(layer).hitboxes = collisions.calculate_strut_hitboxes(
                self.strutsets.get(layer)
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
            sprite_pos = (sprite.position.x, sprite.position.y)

            # TODO: order desires?

            update_flag = self.iterations % sprite_props.poll == 0

            for sprite_desire in sprite_desires:

                if sprite_desire.plot != self.plot or sprite.intent:
                    continue

                if update_flag:
                    log.infinite(
                        f'Checking {sprite_key} {sprite_desire.mode} desire conditions...',
                        '_ruminate'
                    )
                    if sprite_desire.mode == 'approach':
                        if 'aware' in sprite_desire.conditions:
                            desire_pos = impulse.locate_desire(
                                sprite_desire.target,
                                self.get_sprites(),
                                sprite.memory.paths
                            )
                            distance = calculator.distance(
                                desire_pos,
                                sprite_pos
                            )
                            if distance <= sprite_props.radii.aware.approach:

                                log.debug(
                                    f'{sprite_key} aware of {sprite_desire.target}...',
                                    '_ruminate'
                                )
                                if sprite.path != sprite_desire.target:
                                    sprite.path = sprite_desire.target
                                self._reorient(sprite_key)
                                break

                            elif distance > sprite_props.radii.aware.approach \
                                    and sprite.path == sprite_desire.target:

                                log.debug(
                                    f'{sprite_key} unaware of {sprite_desire.target}...',
                                    '_ruminate'
                                )
                                sprite.path = None
                                continue

                        elif 'always' in sprite_desire.conditions:
                            log.verbose(
                                f'{sprite_key} always desires {sprite_desire.mode} {sprite_desire.target}...',
                                '_ruminate'
                            )
                            sprite.path = sprite_desire.target
                            self._reorient(sprite_key)
                            break

                    elif sprite_desire.mode == 'engage':
                        pass

                else:
                    # ensure sprite has intent for next iteration
                    if sprite.memory and \
                        sprite.memory.intent and sprite.memory.intent.intention:
                        log.infinite(f'{sprite_key} remembers {sprite.memory.intent.intention} intention',
                                     '_ruminate')
                        sprite.intent = sprite.memory.intent


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
                'emotion': emotion, #
            })
        """

        for sprite_key, sprite in self.get_sprites().items():
            if not sprite.intent or \
                    sprite.stature.action in self.sprite_stature.decomposition.blocking:
                # NOTE: if sprite in blocking stature, no intent is transmitted or consumed
                continue

            log.infinite(
                f'Applying intent {sprite.intent.intention} to {sprite_key}\'s stature: {sprite.stature.intention}',
                '_intend'
            )

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

            if sprite.intent.get('expression') and \
                    sprite.intent.expression != sprite.stature.expression:
                sprite.stature.expression = sprite.intent.expression

            if sprite_key != 'hero':
                sprite.memory.intent = sprite.intent

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
                    self.apparel_stature,
                    self.get_sprites(sprite.layer)
                )
                animate = True

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
                sprite_stature_key = formulae.compose_animate_stature(
                    sprite, self.sprite_stature
                )
                if sprite.frame >= self.sprite_stature.animate_map.get(sprite_stature_key).frames:
                    sprite.frame = 0
                    if sprite.stature.action in self.sprite_stature.decomposition.blocking:
                        sprite.stature.intention = None
                        sprite.stature.action = 'walk'


    def _reorient(
        self,
        sprite_key: str
    ) -> None:

        sprite = self.npcs.get(sprite_key)
        sprite_hitbox = collisions.calculate_sprite_hitbox(
            sprite,
            'strut',
            self.sprite_properties.get(sprite_key)
        )
        collision_set = collisions.collision_set_relative_to(
            'strut',
            None,
            self.strutsets.get(sprite.layer).hitboxes,
            self.platesets.get(sprite.layer).containers,
            self.get_typed_platesets(sprite.layer, 'gate'),
            self.switch_map.get(sprite.layer)
        )
        path = impulse.locate_desire(
            sprite.path,
            self.get_sprites(),
            sprite.memory.paths
        )

        log.verbose(f'Reorienting {sprite_key} to {path}', '_reorient')

        paths.reorient(
            sprite,
            sprite_hitbox,
            collision_set,
            path,
            self.sprite_properties.get(sprite_key).speed.collide,
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

        collision_map = collisions.generate_collision_map(
            self.get_sprites()
        )

        for sprite_key, sprite in self.get_sprites().items():
            for hitbox_key in ['strut', 'sprite']:
                exclusions = [ sprite_key ]
                if hitbox_key == 'sprite':
                    exclusions += [
                        key for key,val in collision_map.get(sprite_key).items() if val
                    ]

                sprite_hitbox = collisions.calculate_sprite_hitbox(
                    sprite,
                    hitbox_key,
                    self.sprite_properties.get(sprite_key)
                )

                if sprite_hitbox is None:
                    continue

                other_sprite_hitboxes = collisions.calculate_sprite_hitboxes(
                    self.get_sprites(sprite.layer),
                    self.sprite_properties,
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
                    self.get_typed_platesets(sprite.layer, 'gate'),
                    self.switch_map.get(sprite.layer)
                )

                log.infinite(
                    f'Checking {sprite_key} for {hitbox_key} collisions...',
                    '_physics'
                )

                collision_box = collisions.detect_collision(
                    sprite_key, 
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
                        self.sprite_properties.get(sprite_key),
                        collision_box
                    )
                    if sprite_key != "hero":
                        sprite_hitbox = collisions.calculate_sprite_hitbox(
                            sprite,
                            hitbox_key,
                            self.sprite_properties.get(sprite_key)
                        )
                        path = impulse.locate_desire(
                            sprite.path,
                            self.get_sprites(),
                            sprite.memory.paths
                        )
                        log.debug(f'Reorienting {sprite_key} with path {sprite.path}',
                                    '_physics')
                        paths.reorient(
                            sprite,
                            sprite_hitbox,
                            collision_set,
                            path,
                            self.sprite_properties.get(sprite_key).speed.collide,
                            self.dimensions
                        )

                if hitbox_key == 'sprite':
                    for key, val in collision_map.copy().items():
                        if key not in exclusions and \
                                key == sprite_key:
                            for nest_key in val.keys():
                                setattr(collision_map.get(key), nest_key, True)
                                setattr(collision_map.get(nest_key), key, True)

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

        for layer in self.layers:
            mass_hitboxes = [ 
                mass.hitbox.strut for mass in self.platesets.get(layer).masses 
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
            filter(lambda x: x.plot == self.plot, sprite.desires)
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
            # for i, plate in enumerate(plate_conf.sets):
            #     typed_platesets.append(
            #         munch.Munch({
            #             'key': plate_key,
            #             'index': i,
            #             'hitbox': plate.hitbox,
            #             'content': plate.content,
            #             'position': plate.start
            #         })
            #     )
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

        .. note::
            This method returns a dict by design, since a Munch would copy the data, but leave the original unaltered. This method
            exposes sprites for alterations. It must be used with care.
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
        user_input: dict
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
