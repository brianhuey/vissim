import numpy as np
from scipy.optimize import fsolve


def offsetParallel(points, distance, clockwise=True):
    """ Create a parallel offset of xy points a certain distance and
        direction from the original.
        Input: list of xy points, distance in meters, direction
        Output: transformed list of xy points
    """
    def perp(a, dist, clockwise=True):
        norm = a/np.linalg.norm(a)*dist
        b = np.empty_like(norm)
        if clockwise:
            b[0] = norm[1]
            b[1] = -norm[0]
        elif not clockwise:
            b[0] = -norm[1]
            b[1] = norm[0]
        return b
    start = None
    offsetPoints = []
    for i, point in enumerate(points):
        point = np.array(point, dtype='float')
        if i == 0:
            start = point
        elif i == 1:
            prev = (perp(start - point, distance,
                    clockwise=(not clockwise)) + start)
            offsetPoints.append(list(np.array(prev, dtype='str')))
            ppoint = (perp(point - start, distance, clockwise=clockwise) +
                      point)
            offsetPoints.append(list(np.array(ppoint, dtype='str')))
            start = point
        else:
            ppoint = (perp(point - start, distance, clockwise=clockwise) +
                      point)
            offsetPoints.append(list(np.array(ppoint, dtype='str')))
            start = point
    return offsetPoints


def offsetEndpoint(points, distance, beginning=True):
    """ Pull back end point of way in order to create VISSIM intersection.
        Input: list of nodes, distance, beginning or end of link
        Output: transformed list of nodes
    """
    if beginning:
        a = np.array(points[1], dtype='float')
        b = np.array(points[0], dtype='float')
    if not beginning:
        a = np.array(points[-2], dtype='float')
        b = np.array(points[-1], dtype='float')
    if np.sqrt(sum((b-a)**2)) < distance:
        distance = math.sqrt(sum((b-a)**2)) * 0.99
    db = (b-a) / np.linalg.norm(b-a) * distance
    return b - db


def bezier(origin, destination, n):
    """ Bezier spline interpolation """
    if origin == destination:
        return [origin[1], destination[0]]
    origin = np.array(origin, dtype=float)
    destination = np.array(destination, dtype=float)
    o1x, o1y, o1z = origin[0]  # origin from point
    o2x, o2y, o2z = origin[1]  # origin end point
    d1x, d1y, d1z = destination[1]  # destination from point
    d2x, d2y, d2z = destination[0]  # destination end point
    # origin slope and intercept
    om = (o2y-o1y) / float(o2x-o1x)
    ob = o1y - (om * o1x)
    # destination slope and intercept
    dm = (d2y-d1y) / float(d2x-d1x)
    db = d1y - (dm * d1x)
    # control points
    cx = (db - ob) / float(om-dm)
    cy = (om * cx) + ob
    t = np.linspace(0, 1, num=n)
    # Quadratic Bezier equations
    Bx = (1-t)**2*o2x + 2*(1-t)*t*cx + t**2*d2x
    By = (1-t)**2*o2y + 2*(1-t)*t*cy + t**2*d2y
    Bz = [0] * n
    # Bounding box
    if om * dm > 0:
        return [origin[1], destination[0]]
    else:
        return zip(Bx, By, Bz)
