from onta import device


def format_breakpoints(
    break_points: list
) -> list:
    """_summary_

    :param break_points: _description_
    :type break_points: list
    :return: _description_
    :rtype: list
    """
    return [
        (break_point['w'], break_point['h']) 
            for break_point in break_points
    ]

def rotate_dimensions(
    rotator: dict, 
    direction: str
) -> tuple:
    """The width and height of a cap relative to a direction, `vertical` or `horizontal`.

    :param cap: _description_
    :type cap: _type_
    :param direction: _description_
    :type direction: _type_
    :return: _description_
    :rtype: _type_
    """
    if rotator['definition'] in ['left', 'right', 'horizontal']:
        if direction =='horizontal':
            return (
                rotator['size']['w'], 
                rotator['size']['h']
            )
        if direction == 'vertical':
            return (
                rotator['size']['h'], 
                rotator['size']['w']
            )
    elif rotator['definition'] in ['up', 'down', 'vertical']:
        if direction == 'horizontal':
            return (
                rotator['size']['h'], 
                rotator['size']['w']
            )
        if direction == 'vertical':
            return (
                rotator['size']['w'], 
                rotator['size']['h']
            )

def find_media_size(
    player_device: device.Device, 
    sizes: list, 
    breakpoints: list
) -> str:
    """_summary_

    :param player_device: _description_
    :type player_device: device.Device
    :param sizes: _description_
    :type sizes: list
    :param breakpoints: _description_
    :type breakpoints: list
    :return: _description_
    :rtype: str
    """
    dim = player_device.dimensions
    for i, break_point in enumerate(breakpoints):
        if dim[0] < break_point[0] and dim[1] < break_point[1]:
            return sizes[i]
    return sizes[len(sizes)-1]