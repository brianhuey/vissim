import numpy as np
import math


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
        return b

    tmp = np.array(points)
    A=tmp.astype(np.float)
    #print points	
    #print "A is",A	
    B = np.vstack([-A[1], A[0], A[1:-1]])
    #print "B is",B
    #print "A-B is", A-B 	
    return np.array(perp(A-B, distance) + A, dtype='str')


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


def inRange(p,q,r):
    """
	return true iff q is between p and r
    """
    return ( (p <=q <= r) or (r<=q<=p) )


def getDistance(point1, point2):
    """ 
	point1 and point2 to be x,y,z coordinates
	Returns the length of the segment between the two points
    """
    tmp1= np.array(point1)
    x1,y1,z1 = tmp1.astype(np.float)
    tmp2= np.array(point2)
    x2,y2,z2 = tmp2.astype(np.float)
    d = (x2-x1) **2 + (y2-y1)** 2 + (z2-z1)**2
    dist = math.sqrt(d)
    return dist


def getNearestPointOnLine(point1, line):
    """
	point1 is a given point
	line is rep by 2 points
	find the point on line where perp drawn from point1 meets the line
    """
    # first convert line to normalized unit vector
    ptA = (np.array(line[0])).astype(np.float)
    ptB = (np.array(line[1])).astype(np.float)
    x1,y1,z1 = ptA
    x2,y2,z2 = ptB
    #
    sepVec = ptA - ptB
    x3,y3,z3 = (np.array(point1).astype(np.float))
    mag = np.sqrt(sepVec.dot(sepVec))
    dx=sepVec[0]
    dy=sepVec[1]
    dz=sepVec[2]
    dx = dx/mag
    dy = dy/mag
    dz = dz/mag
    # translate the point and get the dot product
    lambda1 = dx * (x3 - x1) 
    lambda2 = dy * (y3 - y1)
    lambda3 = dz * (z3 - z1)
    lam = lambda1 + lambda2 + lambda3
    x4 = (dx * lam) + x1;
    y4 = (dy * lam) + y1;
    z4 = (dz * lam) + z1;
    return x4,y4,z4

def getNearestPointOnSegment(point1, segment):
    """
	point1 is a given point
	segment is rep by 2 points
	find the point on segment where perp drawn from point1 meets the segment
	if the nearest point lies outside the segment, return nan
    """
    ptA = (np.array(segment[0])).astype(np.float)
    ptB = (np.array(segment[1])).astype(np.float)
    x1,y1,z1 = ptA
    x2,y2,z2 = ptB
    x3,y3,z3 =  getNearestPointOnLine(point1, segment)
    if (inRange(x1,x3,x2) and inRange(y1,y3,y2) ) : # ignoring z 
    	return (x3,y3,z3)
    else:
	#print 'perp falls outside the segment'
	return None
