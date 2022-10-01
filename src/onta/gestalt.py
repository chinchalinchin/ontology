import sys
import munch
import threading
from PySide6 \
    import QtWidgets, QtGui, QtCore
from PIL import Image

from onta \
    import world
from onta.actuality \
    import datum
from onta.concretion \
    import composition, taxonomy
from onta.concretion.facticity \
    import gauge, formulae
from onta.metaphysics \
    import device, logger, gui, debug, settings
from onta.qualia \
    import intrinsic, extrinsic
from onta.qualia.thoughts \
    import bauble

log = logger.Logger(
    'onta.gestalt', 
    settings.LOG_LEVEL
)

## GUI Handlers

def get_app(
) -> QtWidgets.QApplication:
    app = QtWidgets.QApplication([])
    return app


def quit(
    app: QtWidgets.QApplication
) -> None:
    sys.exit(app.exec_())


def position(
    view_widget: QtWidgets.QWidget,
    position: str = 'center'
) -> QtWidgets.QWidget:
    if position == 'center':
        position = QtGui.QScreen.availableGeometry(
            QtWidgets.QApplication.primaryScreen()
        ).center()
    elif position == 'bottom_left':
        position = QtGui.QScreen.availableGeometry(
            QtWidgets.QApplication.primaryScreen()
        ).bottomLeft()

    geo = view_widget.frameGeometry()
    geo.moveCenter(position)
    view_widget.move(geo.topLeft())
    QtGui.QScreen.availableGeometry(
        QtWidgets.QApplication.primaryScreen()
    ).bottom()
    return view_widget


## GUI Widgets & Workers


class Debugger(QtCore.QObject):
    update = QtCore.Signal(bool)

    def start(self):
        threading.Timer(
            settings.DEBUG_TIMER, 
            self._execute
        ).start()

    def _execute(self):
        threading.Timer(
            settings.DEBUG_TIMER, 
            self._execute
        ).start()
        self.update.emit(True)


class ScrollLabel(QtWidgets.QScrollArea):
 
    def __init__(
        self, 
        *args, 
        **kwargs
    ):
        QtWidgets.QScrollArea.__init__(
            self, 
            *args, 
            **kwargs
        )
        self.setWidgetResizable(True)
        content = QtWidgets.QWidget(self)
        self.setWidget(content)
        lay = QtWidgets.QVBoxLayout(content)
        self.label = QtWidgets.QLabel(content)
        self.label.setAlignment(
            QtGui.Qt.AlignLeft | QtGui.Qt.AlignTop
        )
        self.label.setWordWrap(True)
        lay.addWidget(self.label)
 
    def setText(
        self, 
        text: str
    ) -> None:
        self.label.setText(text)


class Renderer():
    """_summary_
    """

    def __init__(
        self, 
        game_world: world.World, 
        data_totality: datum.Totality, 
        player_device: device.Device,
        debug: bool = False
    ):
        """
        .. note:
            No references are kept to `static_world` or `repository`.
        """
        self.last_layer = game_world.layer
        self.player_device = player_device
        self.static_cover_frame = munch.Munch({
            layer: gui.new_image(game_world.dimensions) 
            for layer 
            in game_world.layers
        })
        self.static_back_frame = munch.Munch({
            layer: gui.new_image(game_world.dimensions)
            for layer 
            in game_world.layers
        })

        self._render_tiles(
            game_world, 
            data_totality
        )
        self._render_sets(
            game_world, 
            data_totality
        )
        self.debug = debug
        self.debug_templates = munch.Munch({})
        self.debug_worker = None
        self.world_frame = None


    def _render_tiles(
        self, 
        game_world: world.World, 
        data_totality: datum.Totality
    ) -> None:
        """Renders static tilesets onto the static world frames. This method is only called once per session, when the game engine is initializing.


        :param game_world: _description_
        :type game_world: world.World
        :param repository: _description_
        :type repository: repo.Repo
        """
        log.debug(
            'Rendering tile sets', 
            'Renderer._render_tiles'
        )

        for layer in game_world.layers:
            for group_key, group_conf in game_world.get_tilesets(layer).items():
                log.verbose(
                    f'Rendering {group_key} tiles', 
                    'Renderer._render_tiles'
                )

                group_tile = data_totality.get_form_frame(
                    taxonomy.FormType.TILE.value, 
                    group_key
                )

                for set_conf in group_conf.sets:
                    start = gauge.scale(
                        ( 
                            set_conf.start.x, 
                            set_conf.start.y 
                        ), 
                        game_world.tile_dimensions,
                        set_conf.start.units
                    )
                    set_dim = ( 
                        set_conf.multiply.w, 
                        set_conf.multiply.h
                    )

                    log.verbose(
                        f'Rendering at {start} with dimensions {set_dim}', 
                        'Renderer._render_tiles'
                    )
                    
                    coordinates = formulae.tile_coordinates(
                        set_dim,
                        start,
                        game_world.tile_dimensions
                    )
                    for coord in coordinates:
                        if set_conf.get('cover'):
                            gui.render_paste(
                                self.static_cover_frame.get(layer),
                                group_tile,
                                coord
                            )
                            continue
                        
                        gui.render_paste(
                            self.static_back_frame.get(layer),
                            group_tile,
                            coord
                        )


    def _render_sets(
        self, 
        game_world: world.World, 
        data_totality: datum.Totality
    ) -> None:
        """Renders static strutsets (and door platesets) onto the static world frames. This method is only called once per session, when the game engine is initializing.

        :param game_world: _description_
        :type game_world: world.World
        :param repository: _description_
        :type repository: repo.Repo

        .. note:
            Only _Doors_ are considered static platesets. All other types of plates need to be re-rendered. Therefore, this method will only render _Door_ plates. It makes it a bit awkward in terms of logic, but results in better performance. Otherwise, doors would be re-rendered every cycle in `_render_variable_platesets`.
        """
        log.debug(
            'Rendering strut and plate sets', 
            'Renderer._render_sets'
        )
    
        for layer in game_world.layers:
            strutsets =  game_world.get_strutsets(layer)
            platesets = game_world.get_platesets(layer)
            strut_keys = list(strutsets.keys())
            unordered_groups = strutsets
            unordered_groups.update(platesets)

            render_map = gui.order_render_dict(unordered_groups)
            # TODO: render map doesn't work...should be able to iterate over it instaed of 
            # unordered groups,but the independence of plate and strut order needs more thought,
            # i.e. how to coalesce the separate strut and plate orders?

            # NOTE: this method only renders static plates. See note in docstring.
            for group_key, group_conf in unordered_groups.items():
                if group_key in strut_keys or \
                    (
                        game_world.plate_properties.get(group_key) and \
                        game_world.plate_properties.get(group_key).type in \
                            list(taxonomy.StaticPlateFamily.__members__.values())
                    ):

                    group_type  = taxonomy.FormType.STRUT.value \
                        if group_key in strut_keys else \
                        taxonomy.FormType.PLATE.value 

                    log.verbose(
                        f'Rendering {group_type} {group_key}s', 
                        'Renderer._render_sets'
                    )
                    group_frame = data_totality.get_form_frame(
                        group_type, 
                        group_key
                    )

                    for set_conf in group_conf.sets:
                        start = gauge.scale(
                            ( 
                                set_conf.start.x, 
                                set_conf.start.y 
                            ), 
                            game_world.tile_dimensions,
                            set_conf.start.units
                        )
                        log.verbose(
                            f'Rendering at {start}', 
                            'Renderer._render_sets'
                        )

                        if set_conf.get('cover'):
                            gui.render_composite(
                                self.static_cover_frame.get(layer),
                                group_frame,
                                start
                            )
                            continue

                        gui.render_composite(
                            self.static_back_frame.get(layer),
                            group_frame,
                            start
                        )
    

    def _render_variable_platesets(
        self, 
        game_world: world.World, 
        data_totality: datum.Totality,
        crop: bool
    ) -> None:
        unordered_groups = game_world.get_platesets(game_world.layer)
        render_map = gui.order_render_dict(unordered_groups)    
        player_dim = (
            game_world.hero.position.x,
            game_world.hero.position.y,
            game_world.sprite_dimensions[0],
            game_world.sprite_dimensions[1]
        )

        # TODO: what if not on screen? currently being handled by formulae
        #       module, but should be handled in this method.

        # and anyway, plates need rendered by type.
        #   first pressures and then everything else
        for group_key, group_conf in render_map.items():
            group_frame = data_totality.get_form_frame(
                taxonomy.FormType.PLATE.value, 
                group_key
            )
            group_type = game_world.plate_properties.get(group_key).type

            log.infinite(
                f'Rendering {group_type} {group_key} plates', 
                'Renderer._render_variable_platesets'
            )

            if group_type in list(
                e.value 
                for e 
                in taxonomy.StaticPlateFamily.__members__.values()
            ):
                continue

            if group_type not in list(
                e.value 
                for e
                in taxonomy.SwitchPlateFamily.__members__.values()
            ):
                group_dim = (
                    group_frame.size[0],
                    group_frame.size[1]
                )
            else:
                group_dim = (
                    group_frame.on.size[0],
                    group_frame.on.size[1]
                )
    
            # NOTE: convert to immutable tuple of tuples for cython static typing
            typeable_group_conf = tuple(
                (
                    set_conf.start.x,
                    set_conf.start.y, 
                    set_conf.start.units
                )
                for set_conf 
                in group_conf['sets']
            )

            if not typeable_group_conf:
                continue

            # NOTE: pass immutable args to cython for static typing
            coordinates = formulae.plate_coordinates(
                typeable_group_conf,
                player_dim,
                group_dim,
                game_world.tile_dimensions,
                game_world.dimensions,
                self.player_device.dimensions,
                crop
            )

            # NOTE: due to player interaction, plate coordinates can be floats.
            #       therefore, cast to ints before passing to PIL.
            for coord in coordinates:

                log.infinite(
                    f'Rendering at ({coord[1]},{coord[2]})', 
                    'Renderer._render_variable_platesets'
                )

                if group_type not in list(
                    e.value 
                    for e
                    in taxonomy.SwitchPlateFamily.__members__.values()
                ):
                    gui.render_composite(
                        self.world_frame,
                        group_frame,
                        # NOTE: coord contains index of plate, so cannot pass it in directly
                        gui.int_tuple(
                            ( 
                                coord[1], 
                                coord[2] 
                            )
                        )
                    )
                    continue

                if game_world.switch_map.get(game_world.layer).get(group_key).get(
                    str(coord[0])    
                ):
                    gui.render_composite(
                        self.world_frame,
                        group_frame.on,
                        gui.int_tuple(
                            ( 
                                coord[1], 
                                coord[2] 
                            )
                        )
                    )
                    continue

                gui.render_composite(
                    self.world_frame,
                    group_frame.off,
                    gui.int_tuple(
                        ( 
                            coord[1], 
                            coord[2] 
                        )
                    )
                )


    def _render_static(
        self, 
        layer_key: str, 
        cover: bool = False
    ) -> None:
        """_summary_

        :param layer_key: _description_
        :type layer_key: str
        :param cover: _description_, defaults to False
        :type cover: bool, optional
        :return: _description_
        :rtype: _type_

        .. note::
            - This method will create a new `self.world_frame` when `cover == False`, i.e. it will overwrite the current world frame with a blank image when it is redrawing the background.
        """

        if cover:
            return gui.render_composite(
                self.world_frame,
                self.static_cover_frame.get(layer_key),
                ( 0,0 )
            )

        self.world_frame = gui.new_image(
            self.static_back_frame.get(layer_key).size
        )

        return gui.render_composite(
            self.world_frame,
            self.static_back_frame.get(layer_key),
            ( 0, 0 )
        )


    def _render_sprites(
        self,
        game_world: world.World, 
        data_totality: datum.Totality,
        crop: bool
    ) -> None:
        """_summary_

        :param game_world: _description_
        :type game_world: world.World
        :param repository: _description_
        :type repository: repo.Repo

        .. note::
            Base frame gets rendered no matter what, while accent frames only get rendered if sprite does not have armor equipped. If armor is equipped, armor frames are rendered in place.
        .. note::
            Equipment frame only gets rendered if it is binded to a sprite state in the apparel configuration file. 
        """
        unordered_sprites = game_world.get_sprites(game_world.layer)
        ordered_sprites = gui.order_sprite_dict(unordered_sprites)
        player_dim = (
            game_world.hero.position.x,
            game_world.hero.position.y,
            game_world.sprite_dimensions[0],
            game_world.sprite_dimensions[1]
        )

        for sprite_key, sprite in ordered_sprites.items():
            sprite_position = gui.int_tuple(
                ( 
                    sprite.position.x, 
                    sprite.position.y 
                )
            )

            sprite_stature_key = composition.compose_animate_stature(
                sprite,
                game_world.sprite_stature
            )
            # BASE RENDERING
            sprite_base_frame, sprite_accent_frame = \
                data_totality.get_sprite_frame(
                    sprite_key, 
                    sprite_stature_key, 
                    sprite.frame
                )

            sprite_dim = (
                sprite_position[0],
                sprite_position[1],
                sprite_base_frame.size[0],
                sprite_base_frame.size[1]
            )

            if crop and not formulae.on_screen(
                player_dim,
                sprite_dim,
                self.player_device.dimensions,
                game_world.dimensions,
            ):
                continue

            gui.render_composite(
                self.world_frame,
                sprite_base_frame,
                sprite_position
            )

            # ARMOR RENDERING
            if sprite.armor:
                animate_statures = \
                    game_world.apparel_properties.armor.get(sprite.armor).animate_statures

                if (isinstance(animate_statures, str) and \
                        animate_statures == 'all') or \
                    (isinstance(animate_statures, list) and \
                        sprite_stature_key in animate_statures):

                    armor_frame = data_totality.get_apparel_frame(
                        taxonomy.ApparelType.ARMOR.value,
                        sprite.armor,
                        sprite_stature_key,
                        sprite.frame
                    )
                    gui.render_composite(
                        self.world_frame,
                        armor_frame,
                        sprite_position
                    )

            elif sprite_accent_frame:
                gui.render_composite(
                    self.world_frame,
                    sprite_accent_frame,
                    sprite_position
                )

            # EQUIPMENT RENDERING
            if any(
                slot 
                for slot 
                in sprite.slot.values()
            ):
                enabled = [ 
                    slot 
                    for slot 
                    in sprite.slot.values() 
                    if slot 
                ]

                for enabled_equipment in enabled:
                    animate_statures = \
                        game_world.apparel_properties.equipment.get(enabled_equipment).animate_statures


                    if (
                            isinstance(
                                animate_statures, 
                                str
                            ) 
                            and animate_statures == 'all'
                        ) or \
                        (   
                            isinstance(
                                animate_statures, 
                                list
                            ) 
                            and sprite_stature_key in animate_statures
                        ):

                        equipment_frame = data_totality.get_apparel_frame(
                            taxonomy.ApparelType.EQUIPMENT.value,
                            enabled_equipment,
                            sprite_stature_key,
                            sprite.frame
                        )
                        gui.render_composite(
                            self.world_frame,
                            equipment_frame,
                            sprite_position
                        )

            if sprite.stature.expression:
                expression_frame = data_totality.get_expression_frame(
                    sprite.stature.expression
                )
                position = (
                    sprite.position.x + ( 
                        game_world.sprite_dimensions[0] - expression_frame.size[0] 
                    ) / 2,
                    sprite.position.y
                )
                gui.render_composite(
                    self.world_frame,
                    expression_frame,
                    gui.int_tuple(position)
                )


    def _render_projectiles(
        self,
        game_world: world.World,
        repository: datum.Totality,
        crop: bool
    ) -> None:
        player_dim = (
            game_world.hero.position.x,
            game_world.hero.position.y,
            game_world.sprite_dimensions[0],
            game_world.sprite_dimensions[1]
        )
        for projectile in game_world.projectiles:
            projectile_frame = repository.get_projectile_frame(
                projectile.key, 
                projectile.direction
            )
            projectile_dim = (
                projectile.current[0],
                projectile.current[1],
                game_world.projectile_properties.get(projectile.key).size.w,
                game_world.projectile_properties.get(projectile.key).size.h
            )

            if crop and not formulae.on_screen(
                player_dim,
                projectile_dim,
                self.player_device.dimensions,
                game_world.dimensions,
            ):
                continue

            gui.render_composite(
                self.world_frame,
                projectile_frame,
                (
                    projectile_dim[0], 
                    projectile_dim[1]
                )
            )


    def _render_extrinsic_quales(
        self, 
        display: extrinsic.ExtrinsicQuale, 
        data_totality: datum.Totality
    ) -> None:

        ### SLOT RENDERING
        rendering_points = display.get_render_points(
            taxonomy.ExtrinsicType.SLOT.value
        )

        cap_dir = display.get_cap_directions()
        buffer_dir = display.get_buffer_direction()

        # slot names
        render_order = iter(display.properties.slot.maps)

        cap_frames = data_totality.get_slot_frames(
            display.media_size, 
            taxonomy.SlotPiece.CAP.value
        )
        buffer_frames = data_totality.get_slot_frames(
            display.media_size, 
            taxonomy.SlotPiece.BUFFER.value
        )
        # TODO: I don't like the view creating the data structure here...
        # this should be done in repo...
        slot_frames = munch.Munch({
            taxonomy.SlotPiece.ENABLED.value: 
                data_totality.get_slot_frames(
                    display.media_size, 
                    taxonomy.SlotPiece.ENABLED.value
                ),
            taxonomy.SlotPiece.DISABLED.value:  
                data_totality.get_slot_frames(
                    display.media_size, 
                taxonomy.SlotPiece.DISABLED.value
                ),
            taxonomy.SlotPiece.ACTIVE.value: 
                data_totality.get_slot_frames(
                    display.media_size, 
                    taxonomy.SlotPiece.ACTIVE.value
                )
        })


        # cap, then alternate buffer and slot until last cap
        for i, render_point in enumerate(rendering_points):
            if i == 0:
                render_frame = cap_frames.get(cap_dir[0])

            elif i == len(rendering_points) -1:
                render_frame = cap_frames.get(cap_dir[1])

            elif i % 2 == 0:
                render_frame = buffer_frames.get(buffer_dir)

            else:
                render_key = next(render_order)
                # map from slot name -> slot state -> slot frame
                render_frame = slot_frames.get(
                    display.get_frame_map(
                        taxonomy.ExtrinsicType.SLOT.value
                    ).get(render_key)
                )

                log.infinite(
                    f'Rendering {render_key} slot...',
                    'Renderer._render_extrinsic_quales'
                )

            gui.render_composite(
                self.world_frame,
                render_frame,
                gui.int_tuple(render_point)
            )
        
        ## MIRROR RENDERING
        rendering_points = display.get_render_points(
            taxonomy.MirrorType.LIFE.value
        )

        log.infinite(
            f'Rendering {taxonomy.MirrorType.LIFE.value} mirrors...',
            'Renderer._render_extrinsic_quales'
        )

        for i, frame_key in display.get_frame_map(
            taxonomy.MirrorType.LIFE.value
        ).items():
            life_frame = data_totality.get_mirror_frame(
                display.media_size, 
                taxonomy.MirrorType.LIFE.value, 
                frame_key
            )
            render_point = rendering_points[i]
            gui.render_composite(
                self.world_frame,
                life_frame,
                gui.int_tuple(render_point)
            )

        ## PACK RENDERING
        # avatar rendering points include slot avatars and wallet avatars...
        for pack_key in taxonomy.PackType.__members__.values():
            log.infinite(
                f'Rendering {pack_key.value} pack...',
                'Renderer._render_extrinsic_quales'
            )

            pack_map = display.get_frame_map(pack_key.value)
            pack_rendering_points = display.get_render_points(pack_key.value)

            for i, render_point in enumerate(pack_rendering_points):
                # offset by slots

                pack_frame = data_totality.get_pack_frame(
                    display.media_size,
                    pack_key.value,
                    pack_map[i]
                )
                gui.render_composite(
                    self.world_frame,
                    pack_frame,
                    gui.int_tuple(render_point)
                )

        ## AVATAR RENDERING
        avatar_rendering_points = display.get_render_points(
            taxonomy.SelfTypes.AVATAR.value
        )
        avatar_frame_map = display.get_frame_map(
            taxonomy.SelfTypes.AVATAR.value
        )
        # TODO: there has to be a way of calculating this...
        avatar_set_map = munch.Munch({
            taxonomy.AvatarType.ARMORY.value: 4, # slots 
            taxonomy.AvatarType.INVENTORY.value: 8 # slots + wallets + belt + bag
        })

        for i, render_point in enumerate(avatar_rendering_points):
            if not render_point or \
                not avatar_frame_map[str(i)]:
                continue

            if i < avatar_set_map.armory and \
                i < avatar_set_map.inventory:

                set_key = taxonomy.AvatarType.ARMORY.value

            elif i >= avatar_set_map.armory and \
                i < avatar_set_map.inventory:

                set_key = taxonomy.AvatarType.INVENTORY.value

            else: 

                set_key = None

            if not set_key:
                continue

            log.infinite(
                f'Rendering {set_key} avatar...',
                'Renderer._render_extrinsic_quales'
            )
        
            avatar_frame = data_totality.get_avatar_frame(
                set_key,
                avatar_frame_map[str(i)]
            )
            gui.render_composite(
                self.world_frame,
                avatar_frame,
                gui.int_tuple(render_point)
            )

    def _render_intrinsic_quales(
        self, 
        in_quale: intrinsic.IntrinsicQuale, 
        data_totality: datum.Totality
    ) -> None:

        gui.replace_alpha(
            self.world_frame, 
            in_quale.alpha
        )
        overlay = gui.channels(
            self.player_device.dimensions, 
            in_quale.theme.overlay
        )

        self.world_frame.paste(
            overlay, 
            ( 0, 0 ), 
            overlay
        )

        idea_render_pts = in_quale.rendering_points(
            taxonomy.IntrinsicType.IDEA.value
        )
        
        idea_frame_map, idea_piece_map = in_quale.idea_maps()

        for i, render_point in enumerate(idea_render_pts):
            render_frame = data_totality.get_piecewise_qualia_frame(
                in_quale.media_size, 
                taxonomy.IntrinsicType.IDEA.value,
                idea_frame_map[i],
                idea_piece_map[i]
            )
            gui.render_composite(
                self.world_frame,
                render_frame,
                gui.int_tuple(render_point)
            )

        if in_quale.active_thought:
            activated_thought = in_quale.get_active_thought()

            if isinstance(activated_thought, bauble.BaubleThought):
                baub_render_pts, avtr_render_pts = \
                    activated_thought.rendering_points(
                        taxonomy.IntrinsicType.BAUBLE.value
                    )
                baub_frame_map, baub_piece_map, baub_avtr_map = \
                    activated_thought.bauble_maps()

                for i, render_point in enumerate(baub_render_pts):                    
                    if not baub_frame_map[i] or not baub_piece_map[i]:
                        continue

                    render_frame = data_totality.get_piecewise_qualia_frame(
                        in_quale.media_size,
                        taxonomy.IntrinsicType.BAUBLE.value,
                        baub_frame_map[i],
                        baub_piece_map[i]
                    )
                    gui.render_composite(
                        self.world_frame,
                        render_frame,
                        gui.int_tuple(render_point)
                    )

                    if not baub_avtr_map[i]:
                        # NOTE: evaluate separately since baubles don't necessarily contain avatars
                        continue
                    
                    # TODO: why is this not hidden behind the thought interface?
                    avatarset_key = activated_thought.map_avatar_to_set(baub_avtr_map[i])

                    avatar_frame = data_totality.get_avatar_frame(
                        avatarset_key,
                        baub_avtr_map[i]
                    )
                    gui.render_composite(
                        self.world_frame,
                        avatar_frame,
                        gui.int_tuple(avtr_render_pts[i])
                    )
                    
    @QtCore.Slot()
    def _update_debug_view(
        self,
        view_widget: QtWidgets.QWidget
    ):
        """Use the current value for `self.debug_templates` to populate the debug widget. This method is slotted into the debug widget when it is instaniated in `self.get_view`.

        :param view_widget: The widget upon which the world frame widget and the debug widget are being rendered. 
        :type view_widget: QtWidgets.QWidget
        
        .. note::
            View hierarchy
            world_view -> vbox layout
                qlabel
                    pixmap
            debug_view -> hbox layout
                qlabel
                qlabel
                qgroupbox -> vbox layout
                    qradio
                    qradio
        """
        debug_layout = view_widget.layout().itemAt(1).widget().layout()
        debug_layout.itemAt(0).widget().setText(
            self.debug_templates.player_state
        )
        debug_layout.itemAt(1).widget().setText(
            self.debug_templates.control_state
        )
        debug_layout.itemAt(2).widget().setText(
            self.debug_templates.world_state
        )


    def render(
        self, 
        game_world: world.World, 
        data_totality: datum.Totality, 
        display: extrinsic.ExtrinsicQuale, 
        pause: intrinsic.IntrinsicQuale,
        crop: bool = True, 
        layer: str = None
    ) -> Image.Image:
        """_summary_

        :param game_world: _description_
        :type game_world: world.World
        :param repository: _description_
        :type repository: repo.Repo
        :param crop: _description_, defaults to True
        :type crop: bool, optional
        :param layer: _description_, defaults to None
        :type layer: str, optional
        :return: _description_
        :rtype: _type_
        """

        if layer is not None:
            layer_buffer = game_world.layer
            game_world.layer = layer

        if not pause.quale_activated:
            self._render_static(
                game_world.layer, 
                False
            )
            self._render_variable_platesets(
                game_world, 
                data_totality, 
                crop
            )
            self._render_sprites(
                game_world, 
                data_totality, 
                crop
            )
            self._render_projectiles(
                game_world, 
                data_totality, 
                crop
            )
            self._render_static(
                game_world.layer, 
                True
            )

        if layer is not None:
            game_world.layer = layer_buffer
            self.last_layer = game_world.layer
            
        if crop:
            world_dim = game_world.dimensions
            hero_pt = ( 
                game_world.hero.position.x, 
                game_world.hero.position.y
            )
            crop_box = formulae.screen_crop_box(
                self.player_device.dimensions, 
                world_dim, 
                hero_pt
            )
            self.world_frame = self.world_frame.crop(crop_box)
        
        if pause.quale_activated:
            self._render_intrinsic_quales(
                pause, 
                data_totality
            )

        if display.quale_activated:
            self._render_extrinsic_quales(
                display, 
                data_totality
            )

        return self.world_frame


    def get_view(
        self
    ) -> QtWidgets.QWidget:
        view_widget, view_layout = \
                QtWidgets.QWidget(), QtWidgets.QVBoxLayout()
        view_frame = QtWidgets.QLabel(view_widget)
        view_widget.resize(*self.player_device.dimensions)
        view_frame.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Expanding, 
                QtWidgets.QSizePolicy.Expanding
            )
        )
        view_layout.addWidget(view_frame)

        if self.debug:
            debug_frame = QtWidgets.QWidget(view_widget)
            debug_layout = QtWidgets.QHBoxLayout()
            debug_layout.addWidget(
                ScrollLabel()
            )
            debug_layout.addWidget(
                ScrollLabel()
            )
            debug_layout.addWidget(
                ScrollLabel()
            )
            debug_frame.setLayout(debug_layout)
            debug_frame.setSizePolicy(
                QtWidgets.QSizePolicy(
                    QtWidgets.QSizePolicy.Expanding, 
                    QtWidgets.QSizePolicy.Minimum
                )
            )
            view_layout.addWidget(debug_frame)
            self.debug_worker = Debugger()
            self.debug_worker.update.connect(
                (
                    lambda i: lambda: self._update_debug_view(i)
                )(view_widget)
            )
            self.debug_worker.start()

        view_widget.setLayout(view_layout)
        return position(view_widget)


    # Rendering connection to GUI
    def view(
        self, 
        game_world: world.World, 
        view_widget: QtWidgets.QWidget, 
        display: extrinsic.ExtrinsicQuale,
        pause: intrinsic.IntrinsicQuale,
        data_totality: datum.Totality,
        user_input: munch.Munch = None
    ) -> QtWidgets.QWidget: 
        """_summary_

        :param game_world: _description_
        :type game_world: world.World
        :param view_widget: _description_
        :type view_widget: QtWidgets.QWidget
        :param display: _description_
        :type display: extrinsic.ExtrinsicQuale
        :param pause: _description_
        :type pause: intrinsic.IntrinsicQuale
        :param repository: _description_
        :type repository: repo.Repo
        :param user_input: _description_, defaults to None
        :type user_input: munch.Munch, optional
        :return: _description_
        :rtype: QtWidgets.QWidget
        """
        cropped = self.render(
            game_world, 
            data_totality, 
            display, 
            pause
        )

        pix = gui.convert_to_gui(cropped)

        view_frame = view_widget.layout().itemAt(0).widget() 
        view_frame.setPixmap(pix)

        if user_input: # then debugging
            setattr(
                self.debug_templates, 
                'player_state', 
                debug.generate_player_template(game_world)
            )
            setattr(
                self.debug_templates, 
                'control_state',
                debug.generate_input_template(user_input)
            )
            setattr(
                self.debug_templates,
                'world_state',
                debug.generate_world_template(game_world)
            )

        return view_widget