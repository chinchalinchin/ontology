import munch

import onta.settings as settings
import onta.device as device
import onta.loader.conf as conf
import onta.loader.state as state
import onta.util.logger as logger
import onta.engine.senses.display as display
import onta.engine.senses.tab as tab

import onta.engine.static.formulae as formulae

log = logger.Logger('onta.engine.senses.menu', settings.LOG_LEVEL)


class Menu():
    frame_maps = munch.Munch({})
    piece_maps = munch.Munch({})
    menu_conf = munch.Munch({})
    buttons = munch.Munch({})
    """
    self.buttons = {
        'tab_1': {
            'left': 'enabled',
            'middle': 'enabled',
            'right': 'enabled'
        },
        # ...
    }
    """
    properties = munch.Munch({})
    styles = munch.Munch({})
    theme = munch.Munch({})
    sizes = []
    breakpoints = []
    button_rendering_points = []
    menu_activated = False
    active_button = None
    active_tab = None
    media_size = None
    alpha = None
    

    # TODO: what is tabs going to be???
    tabs = munch.Munch({})

    def __init__(
        self, 
        player_device: device.Device, 
        ontology_path: str = settings.DEFAULT_DIR
    ) -> None:
        config = conf.Conf(ontology_path)
        state_ao = state.State(ontology_path).get_state('dynamic')
        self._init_conf(config)
        self.media_size = formulae.find_media_size(
            player_device.dimensions, 
            self.sizes, 
            self.breakpoints
        )
        self._init_menu_positions(player_device)
        self._init_tabs(player_device)
        self._init_buttons(state_ao)


    def _init_conf(
        self, 
        config: conf.Conf
    ) -> None:
        configure = config.load_sense_configuration()
        self.menu_conf = configure.menu
        self.sizes = configure.sizes
        self.styles = configure.styles
        self.properties = configure.properties.menu
        self.alpha = configure.transparency
        self.theme = display.construct_themes(configure.theme)
        self.breakpoints = display.format_breakpoints(configure.breakpoints)


    def _init_menu_positions(
        self, 
        player_device: device.Device
    ) -> None:
        menu_margins = (
            self.styles.get(self.media_size).menu.margins.w,
            self.styles.get(self.media_size).menu.margins.h
        )
        menu_padding = (
            self.styles.get(self.media_size).menu.padding.w,
            self.styles.get(self.media_size).menu.padding.h
        )
        menu_stack = self.styles.get(self.media_size).menu.stack
        # all button component pieces have the same pieces, so any will do...
        button_conf = self.menu_conf.get(self.media_size).button.enabled

        # [ (left_w, left_h), (middle_w, middle_h), (right_w, right_h) ]
        dims = [
            ( button_conf.get(piece).size.w, button_conf.get(piece).size.h ) 
            for piece in self.properties.button.pieces
        ]

        full_width = 0
        for dim in dims:
            full_width += dim[0]

        self.button_rendering_points = formulae.button_coordinates(
            dims,
            len(self.properties.tabs),
            len(button_conf),
            full_width,
            player_device.dimensions,
            menu_stack,
            menu_margins,
            menu_padding
        )


    def _init_tabs(
        self,
        player_device: device.Device
    ):
        for tab_key, tab_conf in self.properties.tabs.items():
            setattr(
                self.tabs,
                tab_key,
                tab.Tab(
                    tab_conf.components,
                    self.styles.get(self.media_size).menu.stack,
                    self.button_rendering_points[0],
                    player_device
                )
            )


    def _init_buttons(
        self, 
        state_ao: state.State
    ) -> None:
        """_summary_

        :param state_ao: _description_
        :type state_ao: state.State
        """
        # TODO: calculate based on state information

        # NOTE: this is what creates `self.buttons`
        #       `self.buttons`
        for i, name in enumerate(list(self.properties.tabs.keys())):
            if i == 0:
                self._activate_button(name)
                self.active_button = i
            else:
                self._enable_button(name)


    def _activate_button(
        self, 
        button_key: str
    ) -> None:
        """_summary_

        :param button_key: _description_
        :type button_key: str
        """
        setattr(
            self.buttons,
            button_key,
            munch.Munch({
                piece: 'active' for piece in self.properties.button.pieces
            })
        )


    def _disable_button(
        self, 
        button_key: str
    ) -> None:
        """_summary_

        :param button_key: _description_
        :type button_key: str
        """
        setattr(
            self.buttons,
            button_key,
            munch.Munch({
                piece: 'disabled' for piece in self.properties.button.pieces
            })
        )


    def _enable_button(
        self, 
        button_key: str
    ) -> None:
        """_summary_

        :param button_key: _description_
        :type button_key: str
        """
        setattr(
            self.buttons,
            button_key,
            munch.Munch({
                piece: 'enabled' for piece in self.properties.button.pieces
            })
        )


    def _increment_active_button(
        self
    ) -> None:
        """_summary_
        """
        button_list = list(self.properties.tabs.keys())
        ## TODO: skip disabled buttons
        previous_active = self.active_button
        self.active_button -= 1

        if self.active_button < 0:
            self.active_button = len(button_list) - 1
        
        self._enable_button(button_list[previous_active])
        self._activate_button(button_list[self.active_button])


    def _decrement_active_button(
        self
    ) -> None:
        """_summary_
        """
        button_list = list(self.properties.tabs.keys())
        ## TODO: skip disabled buttons
        previous_active = self.active_button
        self.active_button += 1

        if self.active_button > len(button_list) - 1:
            self.active_button = 0
        
        self._enable_button(button_list[previous_active])
        self._activate_button(button_list[self.active_button])


    def execute_active_button(
        self
    ):
        pass


    def _calculate_button_frame_map(
        self
    ) -> list:
        # NOTE **: frame changes ... 
        frame_map = []
        for piece_conf in self.buttons.values():
            for piece_state in piece_conf.values():
                frame_map.append(piece_state)
        setattr(self.frame_maps, 'button', frame_map)
        return self.frame_maps.button


    def _calculate_button_piece_map(
        self
    ) -> list:
        # NOTE **: ...but pieces stay the same ...
        if not self.piece_maps.get('button'):
            piece_map = []
            for piece_conf in self.buttons.values():
                for piece_key in piece_conf.keys():
                    piece_map.append(piece_key)
            setattr(self.piece_maps, 'button', piece_map)
        return self.piece_maps.button


    def button_maps(
        self
    ) -> tuple:
        return (
            self._calculate_button_frame_map(), 
            self._calculate_button_piece_map()
        )


    def toggle_menu(
        self
    ) -> None:
        self.menu_activated = not self.menu_activated


    def get_rendering_points(
        self, 
        interface_key: str
    ) -> list:
        if interface_key in [ 'button', 'buttons' ]:
            return self.button_rendering_points


    def update(
        self, 
        user_input: munch.Munch
    ) -> None:
        if user_input.up:
            self._increment_active_button()
        elif user_input.down:
            self._decrement_active_button()