import math

import onta.settings as settings

def projection(angle = 45):
    return math.cos(angle*math.pi/180), math.sin(angle*math.pi/180)

def distance(a, b):
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return math.sqrt(dx*dx + dy*dy)

def intersection(rect_a: tuple, rect_b: tuple):
    """ Determines if two rectangles intersect. Rectangles are defined by the coordinate of the upper-left corner (as viewed in screen units, where the down is the positive y-direction), and its dimensions (i.e., width and height)

    :type rect_a:tuple:
    :param rect_a:tuple: (x, y, width, height)

    :type rect_b:tuple:
    :param rect_b:tuple: (x, y, width, height)

    :rtype:bool:
    """
    # verify rectangles have area
    if 0 in [rect_a[2], rect_a[3], rect_b[2], rect_b[3]]:
        return False

    bottom_corner_a = (rect_a[0] + rect_a[2], rect_a[1] + rect_a[3])
    bottom_corner_b = (rect_b[0] + rect_b[2], rect_b[1] + rect_b[3])

    # verify rectangles do not overlap in horizontal direction
    if bottom_corner_a[0] < rect_b[0] or rect_a[0] > bottom_corner_b[0]:
        return False

    # verify rectangles do not overlap in vertical direction
    if bottom_corner_a[1] < rect_b[1] or rect_a[1] > bottom_corner_b[1]:
        return False

    return True

def scale(start, units = 'absolute'):          
    if units == 'tiles':
        return (start[0]*settings.TILE_DIM[0], start[1]*settings.TILE_DIM[1])
    return start
