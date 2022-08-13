import math
from typing import Union
import numba


@numba.jit(nopython=True, nogil=True, fastmath=True)
def center(
    dim: tuple
) -> tuple:
    return (dim[0] + dim[2] /2, dim[1] + dim[3]/2)


@numba.jit(nopython=True, nogil=True, fastmath=True)
def angle_relative_to_center(
    point: tuple,
    center: tuple = (0,0)
) -> float:

    norm = distance(point, center)
    delta = ( point[0] - center[0], point[1] - center[1] )

    cosine = delta[0] / norm

    if cosine == 0:
        return 0

    if delta[0] > 0 and delta[1] > 0 or \
        delta[0] < 0 and delta[1] > 0:
        return 180 * math.acos(cosine) / math.pi
    return 360 - 180 * math.acos(cosine) / math.pi


@numba.jit(nopython=True, nogil=True, fastmath=True)
def projection(
    angle:float = 45
) -> tuple:
    return (
        math.cos(angle*math.pi/180), 
        math.sin(angle*math.pi/180)
    )


@numba.jit(nopython=True, nogil=True, fastmath=True)
def distance(
    a: tuple, 
    b: tuple
) -> float:
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return math.sqrt(dx ** 2 + dy ** 2)


@numba.jit(nopython=True, nogil=True, fastmath=True)
def intersection(
    rect_a: tuple, 
    rect_b: tuple,
) -> bool:
    """Determines if two rectangles intersect. Rectangles are defined by the coordinate of the upper-left corner (as viewed in screen units, where the down is the positive y-direction), and its dimensions (i.e., width and height)


    :param rect_a: _(x,y,w,h)_
    :type rect_a: tuple
    :param rect_b: _(x,y,w,h)_
    :type rect_b: tuple
    :return: `True` if intersection, `False` otherwise.
    :rtype: bool
    """    
    
    dims = [
        rect_a[2], 
        rect_a[3], 
        rect_b[2], 
        rect_b[3]
    ]

    # verify rectangles have area
    if 0 in dims:
        return False

    bottom_corner_a = (
        rect_a[0] + rect_a[2], 
        rect_a[1] + rect_a[3]
    )
    bottom_corner_b = (
        rect_b[0] + rect_b[2], 
        rect_b[1] + rect_b[3]
    )

    # verify rectangles do not overlap in horizontal direction
    if bottom_corner_a[0] < rect_b[0] or \
        rect_a[0] > bottom_corner_b[0]:
        return False

    # verify rectangles do not overlap in vertical direction
    if bottom_corner_a[1] < rect_b[1] or \
        rect_a[1] > bottom_corner_b[1]:
        return False

    return True


@numba.jit(nopython=True, nogil=True, fastmath=True)
def any_intersections(
    rectangle: tuple, 
    rectangle_tuplized_list: tuple
) -> Union[tuple, None]:
    """Determines if a sprite's hitbox has collided with a list of hitboxes

    :param object_key: 
    :type object_key: str
    :param object_hitbox: _description_
    :type object_hitbox: tuple
    :param hitbox_list: _description_
    :type hitbox_list_tuple: tuple
    :return: The hitbox with which the `object` collided, `None` otherwise
    :rtype: Union[tuple, None]

    .. note::
        This method assumes it only cares _if_ a collision occurs, not with _what_ the collision occurs. The hitbox list is traversed and if any one of the contained hitboxes intersects the sprite, `True` is returned. If none of the hitboxes in the list intersect the given sprite, `False` is returned.
    .. note:: 
        The argument is passed in as a tuple because immutability is a requirement for caching.
    .. todo::
        Modify this to return the direction of the collision. Need to recoil sprite based on where the collision came from, not which direction the sprite is heading...

    """
    for other_rect in list(rectangle_tuplized_list):
        if intersection(rectangle, other_rect):
            return other_rect
    return None


@numba.jit(nopython=True, nogil=True, fastmath=True)
def scale(
    point: tuple, 
    factor: tuple, 
    units: str = 'absolute'
) -> tuple:    
    """Scales a coordinate _(x,y)_ by the tile dimensions if the units match, otherwise returns point unaltered.

    :param point: _(x,y))_
    :type point: tuple
    :param factor: _(w,h)_
    :type factor: tuple
    :param units: measurement units, defaults to 'absolute'
    :type units: str, optional
    :return: the scaled coordinate
    :rtype: tuple
    """
    if units == 'tiles':
        return (point[0]*factor[0], point[1]*factor[1])
    return point
