import onta.settings as settings
import onta.util.logger as logger
import onta.engine.calculator as calculator


log = logger.Logger('onta.engine.formulae', settings.LOG_LEVEL)


def decompose_compositions_into_sets(
    layers: list,
    compositions: dict,
    composition_conf: dict,
    tile_dimensions: tuple,
    tilesets: dict,
    strutsets: dict,
    platesets: dict,
) -> tuple:
    """Decompose _Composite_ _Form_\s, or "compositions", into their constituent formsets and append to existing formsets.

    :param layers: List of layers containing compositions.
    :type layers: list
    :param compositions: Dictionary containing the constituent form sets of a composition.
    :type compositions: dict
    :param composition_conf: _Composite_ configuration information.
    :type composition_conf: dict
    :param tile_dimensions: Dimensions of a _Tile_.
    :type tile_dimensions: tuple
    :param tilesets: Existing tilesets in the world. If composition contains tiles, these _Tile_\s will be appended to the tilesets. 
    :type tilesets: dict
    :param strutsets: Existing strutsets in the world. If composition contains struts, these _Strut_\s will be appended to the strutsets.
    :type strutsets: dict
    :param platesets: Existing platesets in the world. If composition contains plates, these _Plate_\s will be appended to the platesets.
    :type platesets: dict
    :return: tu
    :rtype: tuple containing (tilesets, strutsets, platesets) with composition sets appended

    .. note::
        This method must be called before stationary hitboxes are initialized, since this method decomposes compositions into their consistuent sets and appends them to the existing static state. Otherwise, the compositions will not be rendered on the _View_ or interactable within the _World_.
    """
    log.debug(f'Decomposing composite static world state into constituents...', 
        'decompose_compositions')

    decomposition = [
        tilesets.copy(),
        strutsets.copy(),
        platesets.copy()
    ]
    
    # for layer_one, layer_two, ...
    for layer in layers:
        if compositions.get(layer) is None:
            continue

        # for (house, {composition}), (tree_patch, {composition}) ...
        for composite_key, composition in compositions[layer].items():
            log.verbose(f'Decomposing {composite_key} composition...', 
                'decompose_compositions')

            # NOTE: compose_conf = { 'struts': { ... }, 'plates': { ... } }
            #           via compose configuration information (composite.yaml)
            compose_conf = composition_conf[composite_key]

            # NOTE: composition = { 'order': int, 'sets': [ ... ] }
            #           via compose state information (static.yaml)
            for composeset in composition['sets']:
                # NOTE: composeset = { 'start': { ... } }
                #           via compose state information (static.yaml)
                compose_start = calculator.scale(
                    (
                        composeset['start']['x'], 
                        composeset['start']['y']
                    ),
                    tile_dimensions,
                    composeset['start']['units']
                )

                for elementset_key, elementset_conf in compose_conf.items():
                    # NOTE: elementset_conf = { 'element_key': { 'order': int, 'sets': [ ... ] } }
                    #           via compose element configuration (composite.yaml)
                    log.verbose(f'Initializing decomposed {elementset_key} elementset...', 
                        'decompose_compositions')

                    # careful...a composition doesn't necessarily have everything...
                    if elementset_key == 'tiles':
                        buffer_sets = decomposition[0]
                    elif elementset_key == 'struts':
                        buffer_sets = decomposition[1]
                    elif elementset_key == 'plates':
                        buffer_sets = decomposition[2]

                    for element_key, element in elementset_conf.items():
                        log.verbose(f'Initializing {element_key}', 
                            'decompose_compositions')

                        # NOTE: element['sets'] = [ { 'start': {..}, 'cover': bool } ]
                        #            via compose element configuration (composite.yaml)
                        for elementset in element['sets']:
                            log.verbose('Generating strut render order', 
                                'decompose_compositions')
                            
                            # NOTE elementset = { 'start': { ... }, 'cover': bool }
                            #       via compose element configuration (composite.yaml)

                            if not buffer_sets.get(layer):
                                buffer_sets[layer] = {}
                            
                            if not buffer_sets[layer].get(element_key):
                                buffer_sets[layer][element_key] = {}

                            if not buffer_sets[layer][element_key].get('sets'):
                                buffer_sets[layer][element_key]['sets'] = []
                            
                            if not buffer_sets[layer][element_key].get('order'):
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
                        decomposition[0] = buffer_sets
                    elif elementset_key == 'struts':
                        decomposition[1] = buffer_sets
                    elif elementset_key == 'plates':
                        decomposition[2] = buffer_sets
    
    return (decomposition[0], decomposition[1], decomposition[2])
