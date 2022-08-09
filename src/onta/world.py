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

            self.strutsets.get(layer).hitboxes = self._strut_hitboxes(layer) + \
                self.world_bounds
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
        """Creates the _Sprite Intent_\s.

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


    # calculate rest of sprite intents from desires

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
                    sprite,
                    self.sprite_properties.get(sprite_key),
                    self.apparel_stature
                )
                animate = True

            elif sprite.stature.intention == 'express':
                impulse.express(
                    sprite,
                    self.sprite_properties.get(sprite_key)
                )

            elif sprite.stature.intention == 'operate':
                # well, what differentiates using and operaitng then?
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

            #if sprite.stature.action in self.sprite_stature.decomposition.animate:
            if animate:
                sprite.frame += 1

                # construct sprite stature string
                sprite_stature_key = formulae.compose_animate_stature(
                    sprite, self.sprite_stature
                )
                if sprite.frame >= self.sprite_stature.animate_map.get(sprite_stature_key).frames:
                    sprite.frame = 0
                    if sprite.stature.action in self.sprite_stature.decomposition.blocking:
                        sprite.stature.action = 'walk'
                    # if sprite was in blocking state, set to walk_direction


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

        collision_sets = self._collision_sets_relative_to(
            sprite_key,
            sprite.layer,
            'strut'
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
            collision_sets,
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

        collision_map = collisions.generate_collision_map(self.npcs)

        for sprite_key, sprite in self.get_sprites().items():

            # hero collision detection
            if sprite_key == 'hero':
                sprite_hitbox = collisions.calculate_sprite_hitbox(
                    self.hero,
                    'sprite',
                    self.sprite_properties.get('hero')
                )
                collision_sets = self._collision_sets_relative_to(
                    'hero',
                    self.layer,
                    'sprite'
                )

                log.infinite('Checking hero for collisions...',
                             '_physics')

                for collision_set in collision_sets:
                    collision_box = collisions.detect_collision(
                        sprite_key, 
                        sprite_hitbox, 
                        collision_set
                    )
                    if collision_box:
                        log.debug(f'Player collision at ({round(self.hero.position.x)}, {round(self.hero.position.y)})',
                                  '_physics')
                        collisions.recoil_sprite(
                            sprite, 
                            self.sprite_dimensions,
                            self.sprite_properties.get(sprite_key),
                            collision_box
                        )

            # sprite collision detection
            else:
                for hitbox_key in ['sprite', 'strut']:

                    exclusions = [sprite_key]
                    for key, val in collision_map.get(sprite_key).items():
                        if val:
                            exclusions.append(key)

                    sprite_hitbox = collisions.calculate_sprite_hitbox(
                        sprite,
                        hitbox_key,
                        self.sprite_properties.get(sprite_key)
                    )

                    collision_sets = self._collision_sets_relative_to(
                        sprite_key,
                        sprite.layer,
                        hitbox_key
                    )

                    log.infinite(f'Checking {sprite_key} for {hitbox_key} collisions...',
                                 '_physics')

                    collided = False
                    for collision_set in collision_sets:
                        collision_box = collisions.detect_collision(
                            sprite_key,
                            sprite_hitbox, 
                            collision_set
                        )
                        if collision_box:
                            collided = True
                            collisions.recoil_sprite(
                                sprite,
                                self.sprite_dimensions,
                                self.sprite_properties.get(sprite_key),
                                collision_box
                            )
                    if collided:
                        # recalculate hitbox after sprite recoils
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
                            collision_sets,
                            path,
                            self.sprite_properties.get(sprite_key).speed.collide,
                            self.dimensions
                        )

                    for key, val in collision_map.copy().items():
                        if key not in exclusions and \
                                key == sprite_key:
                            for nest_key in val.keys():
                                setattr(collision_map.get(key), nest_key, True)
                                setattr(collision_map.get(nest_key), key, True)

            # mass collision detection
            masses = self.platesets.get(self.layer).masses.copy()
            for mass in masses:
                collision_box = collisions.detect_collision(
                    mass.key, 
                    mass.hitbox.sprite, 
                    [sprite_hitbox]
                )
                if collision_box:
                    plate = self.get_plate(self.layer, mass.key, mass.index)
                    collisions.recoil_plate(
                        plate, 
                        sprite,
                        self.sprite_dimensions,
                        self.sprite_properties.get(sprite_key),
                        collision_box
                    )
                    setattr(
                        plate.hitbox,
                        'sprite',
                        collisions.calculate_set_hitbox(
                            self.plate_properties.get(mass.key).hitbox.sprite,
                            plate,
                            self.tile_dimensions
                        )
                    )
                    setattr(
                        plate.hitbox,
                        'strut',
                        collisions.calculate_set_hitbox(
                            self.plate_properties.get(mass.key).hitbox.strut,
                            plate,
                            self.tile_dimensions
                        )
                    )
                    self.platesets.get(self.layer).masses = self.get_typed_platesets(
                        self.layer,
                        'mass'
                    )

        for layer in self.layers:
            mass_hitboxes = [ 
                mass.hitbox.strut for mass in self.platesets.get(layer).masses 
            ]
            pressures = self.platesets.get(layer).pressures

            if not (mass_hitboxes and pressures):
                continue

            for pressure in pressures:
                collision_box = collisions.detect_collision(
                    pressure.key, 
                    pressure.hitbox, 
                    mass_hitboxes
                )
                if collision_box and \
                    not self.switch_map.get(layer).get(pressure.key).get(str(pressure.index)):
                    log.debug(f'Switching pressure plate {pressure.key} on', '_physics')
                    setattr(
                        self.switch_map.get(layer).get(pressure.key),
                        str(pressure.index),
                        True
                    )
                    connected_gate = self._gate_connection(
                        layer,
                        pressure
                    )
                    if not connected_gate:
                        continue
                    setattr(
                        self.switch_map.get(layer).get(connected_gate.key),
                        str(connected_gate.index),
                        True
                    )

                elif not collision_box and \
                    self.switch_map.get(layer).get(pressure.key).get(str(pressure.index)):
                    log.debug(f'Switching pressure plate {pressure.key} off', '_physics')
                    setattr(
                        self.switch_map.get(layer).get(pressure.key),
                        str(pressure.index),
                        False
                    )
                    connected_gate = self._gate_connection(
                        layer,
                        pressure
                    )
                    if not connected_gate:
                        continue
                    setattr(
                        self.switch_map.get(layer).get(connected_gate.key),
                        str(connected_gate.index),
                        False
                    )
    
                    
        # TODO: plate-to-plate collisions, plate-to-strut collisions
            # in order to do mass-to-mass collisions efficiently, will need a collision map
            # like with sprites, but the rub here is the keys are {mass_key}_{mass_index}
            # i.e., collision map? 
            #   layer -> first_mass_key -> first_mass_index
            #         -> second_mass_key -> second_mass_index


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
            collision_sets.append(npc_hitboxes)

        if (hitbox_key == 'strut' or sprite_key == 'hero') \
                and self.strutsets.get(layer_key).hitboxes is not None:
            collision_sets.append(
                self.strutsets.get(layer_key).hitboxes
            )

        if (hitbox_key == 'strut' or sprite_key == 'hero') \
                and self.platesets.get(layer_key).containers is not None:
            collision_sets.append(
                [container.hitbox for container in self.platesets.get(
                    layer_key).containers]
            )
            collision_sets.append([ 
                gate.hitbox
                for gate in self.get_typed_platesets(layer_key, 'gate')
                if not self.switch_map.get(layer_key).get(gate.key).get(str(gate.index))
            ])
            # doesn't add pressures, gates, doors or masses, as they are handled separately
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
            sets = strut_conf.sets
            for strut in sets:
                strut_hitboxes.append(strut.hitbox)
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
            raw_hitbox = self.sprite_properties.get(
                sprite_key).hitboxes.get(hitbox_key)
            calc_hitbox = (
                sprite.position.x + raw_hitbox.offset.x,
                sprite.position.y + raw_hitbox.offset.y,
                raw_hitbox.size.w,
                raw_hitbox.size.h
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

        for sprite_key, sprite in self.get_npcs(layer).items():
            if exclude is None or \
                    sprite_key not in exclude:
                calculated.append(
                    collisions.calculate_sprite_hitbox(
                        sprite,
                        hitbox_key,
                        self.sprite_properties.get(sprite_key)
                    )
                )
        return calculated


    def _gate_connection(
        self,
        layer,
        pressure
    ) -> Union[munch.Munch, None]:
        connected_gate = [
            munch.Munch({'key': gate.key, 'index': gate.index})
            for gate in self.get_typed_platesets(layer, 'gate')
            if gate.content == pressure.content 
        ]
        if connected_gate:
            return connected_gate.pop()
        return None

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
            for i, plate in enumerate(plate_conf.sets):
                typed_platesets.append(
                    munch.Munch({
                        'key': plate_key,
                        'index': i,
                        'hitbox': plate.hitbox,
                        'content': plate.content,
                        'position': plate.start
                    })
                )
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
