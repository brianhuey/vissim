import numpy as np


def offsetParallel(points, distance, clockwise=True):
    """ Create a parallel offset of xy points a certain distance and
        direction from the original.
        Input: list of xy points, distance in meters, direction
        Output: transformed list of xy points
    """
    def perp(a, dist, clockwise=True):
        norm = a/np.linalg.norm(a, axis=1, keepdims=True)*dist
        b = np.zeros_like(norm)
        if clockwise:
            b[:, 0] = norm[:, 1]
            b[:, 1] = -norm[:, 0]
        elif not clockwise:
            b[:, 0] = -norm[:, 1]
            b[:, 1] = norm[:, 0]
        return bs
    A = np.array(points)
    B = np.vstack([-A[1], A[0], A[1:-1]])
    C = np.vstack([-A[0], A[1:]])
    return np.array(perp(C-B, distance, clockwise=clockwise) + A, dtype='str')


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
        distance = np.sqrt(sum((b-a)**2)) * 0.99
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
    if o2x == o1x or d2x == d1x:
        return [origin[1], destination[0]]
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
    # Looking for opposite slope values, otherwise don't create a curve
    if om * dm > 0:
        return [origin[1], destination[0]]
    else:
        return zip(Bx, By, Bz)
