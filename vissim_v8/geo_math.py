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


def solveK(points11, points12, points21, points22):
    x1, y1, z1 = points12
    dy1 = (y1-points11[1]) / (x1-points11[0])
    x2, y2, z2 = points12
    dy2 = (y2-points22[1]) / (x2-points22[0])

    def k1(r, h):
        return -np.sqrt(r**2 - (x1-h)**2) + y1

    def k2(r, h):
        return -np.sqrt(r**2 - (x2-h)**2) + y2

    def r1(h):
        return np.sqrt(((-2*x1+h)/(2*dy1))**2 + (x1-h)**2)

    def r2(h):
        return np.sqrt(((-2*x2+h)/(2*dy2))**2 + (x2-h)**2)

    def k1k2r1r2(h):
        k = [k1(h[2], h[0]) - h[1], k2(h[2], h[0]) - h[1], r1(h[0]) - h[2]]
        return k

    return fsolve(k1k2r1r2, [0, 0, 1])


def spline(points11, points12, points21, points22, n):
    points11 = np.array(points11, dtype=float)
    points12 = np.array(points12, dtype=float)
    points21 = np.array(points21, dtype=float)
    points22 = np.array(points22, dtype=float)
    x1, y1, z1 = points11
    x2, y2, z2 = points22
    h, k, r = solveK(points11, points12, points21, points22)
    delta = abs(x2 - x1) / float(n-1)
    xi = np.arange(x1, x2+delta, delta)

    def circle(x):
        yStr = [str(round(y, 4)) for y in np.sqrt(r**2 - (x-h)**2) + k]
        xStr = [str(xs) for xs in x]
        return zip(xStr, yStr, '0' * len(x))
    return circle(xi)
