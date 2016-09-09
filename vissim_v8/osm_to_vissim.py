#!/usr/bin/env python
""" VISSIM Tools """
from vissim_objs import Vissim
import networkx as nx
from osm_to_graph import read_osm
from collections import OrderedDict
import numpy as np
import math


class OSM(Vissim):
    def __init__(self, osmFile):
        self.G = read_osm(osmFile)
        self.v = Vissim()
        self.refLat, self.refLng = self.getRefLatLng()
        self.refX, self.refY = self.latLngToMeters(self.refLat, self.refLng)
        self.intersections = self.createIntersectionDict()
        self.xy = self.createLinkDict()
        self.v.createReference(self.refX, self.refY)

    def stringify(self, iterable):
        """ Convert tuple containing numbers to string
            Input: iterable with numbers as values
            Output: tuple with strings as values
        """
        return tuple([str(i) for i in iterable])

    def getRefLatLng(self):
        """ Get reference lat/lng for xy conversion.
            Input: Graph
            Output: lat, long tuple
        """
        latlng = self.G.node.itervalues().next()
        return latlng['lat'], latlng['lon']

    def getLatLng(self, n):
        """ Return lat/lng tuple for a given node.
        """
        return self.G.node[n]['lat'], self.G.node[n]['lon']

    def latLngToMeters(self, lat, lng):
        """ Convert lat/lng to meters from 0,0 point on WGS84 map.
            Input: WGS84 lat/lng
            Output: x,y in meters
        """
        assert abs(lng) <= 180, '%s exceeds longitudinal domain' % (lng)
        extent = 20015085  # height/width in meters of the VISSIM map
        x = lng * extent / 180.0
        y = (math.log(math.tan((90 + lat) * math.pi / 360.0)) /
             (math.pi / 180.0))
        y = y * extent / 180.0
        return x, y

    def nodeToScaledMeters(self, n):
        """ Apply Mercator scaling factor based on latitude to xy points.
            Input: node
            Output: correctly scaled xy
        """
        lat, lng = self.getLatLng(n)
        x, y = self.latLngToMeters(lat, lng)
        scale = 1 / math.cos(math.radians(self.refLat))
        scaleX = ((x - self.refX) / scale)
        scaleY = ((y - self.refY) / scale)
        return (scaleX, scaleY, '0')

    def isExterior(self, n):
        """ If a node has only one neighbor node, it's at the exterior of the
            model.
        """
        if len(set(self.G.successors(n) + self.G.predecessors(n))) == 1:
            # These are one-way start points, or bi-directional end points
            return True
        else:
            return False

    def getExteriorNodes(self):
        """ Get a list of nodes that are on the exterior.
        """
        nodes = []
        for n in self.G.nodes():
            if self.isExterior(n):
                nodes.append(n)
        return nodes

    def getStartNodes(self):
        """ Get a list of nodes that do not overlap when traversed.
        """
        edgeNodes = self.getExteriorNodes()
        for node in edgeNodes:
            for prev, n in nx.dfs_edges(self.G, source=node):
                if n in edgeNodes:
                    edgeNodes.remove(n)
        return edgeNodes

    def getLanes(self, attr):
        """ Determine number of lanes based on OSM attributes.
            Input: OSM attribute
            Output: tuple with number of lanes (forward, backward),
                    False if no lane numbers specified
        """
        lanes = attr['attr'].get('lanes')
        if self.isOneway(attr['attr']):
            if lanes:
                return int(lanes), 0
            else:
                # If no lane spec, return default.
                return 1, 0
        else:
            forward = attr['attr'].get('lanes:forward')
            backward = attr['attr'].get('lanes:backward')
            if forward and backward:
                return int(forward), int(backward)
            elif lanes:
                if int(lanes) % 2 > 0:
                    raise ValueError('Number of lanes is not evenly divisible')
                else:
                    return int(lanes)/2, int(lanes)/2
            else:
                # If no lane spec, return default.
                return 1, 1

    def isOneway(self, attr):
        """ Determine if link is oneway based on OSM attributes.
            Input: OSM attribute
            Output: boolean
        """
        yes = ['yes', 'true', '1', '-1']
        no = ['no', 'false', '0']
        if attr.get('oneway') in yes:
            return True
        elif attr.get('oneway') in no:
            return False
        elif attr.get('highway') == 'motorway':
            return True
        elif attr.get('junction') == 'roundabout':
            return True
        else:
            return False

    def isNewWay(self, fromN, toN, prevAttr):
        """ Determine if the current edge is a new way
            Input: edge nodes, current attribute
            Output: boolean
        """
        if prevAttr is None:
            return False
        newID = self.G.edge[fromN][toN]['id']
        oldID = prevAttr.get('id')
        if newID == oldID:
            return False
        else:
            return True

    def isIntersection(self, n):
        """ If node has more than two connecting nodes, it's an intersection.
        """
        if len(set(self.G.successors(n) + self.G.predecessors(n))) > 2:
            return True
        else:
            return False

    def isForward(self, attr):
        """ Use attr['id'] to determine whether the link is forward or backward
            Input: attr
            Output: True is forward
        """
        if attr.get('id'):
            if attr['id'][-2:] == '-F':
                return True
            elif attr['id'][-2:] == '-B':
                return False

    def compassBearing(self, pointA, pointB):
        """ Calculates the bearing between two points. Source:
            https://gist.github.com/jeromer/2005586
            Input:
            Output: The bearing in degrees
        """
        if (type(pointA) != tuple) or (type(pointB) != tuple):
            raise TypeError("Only tuples are supported as arguments")
        lat1 = math.radians(pointA[0])
        lat2 = math.radians(pointB[0])
        diffLong = math.radians(pointB[1] - pointA[1])
        x = math.sin(diffLong) * math.cos(lat2)
        y = (math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) *
             math.cos(lat2) * math.cos(diffLong)))
        initial = math.atan2(x, y)
        # Now we have the initial bearing but math.atan2 return values
        # from -180 to + 180 which is not what we want for a compass bearing
        # The solution is to normalize the initial bearing as shown below
        initial = math.degrees(initial)
        compass = round((initial + 360) % 360, 1)
        return compass

    def getIntersection(self, node):
        """ Get direction, bearing and lane information for all intersection
            edges. Bearing is calculated from the common intersection node.
            Input: intersection node
            Output: dictionary of intersection attributes
        """
        intersection = {}
        nodePoint = (self.G.node[node]['lat'], self.G.node[node]['lon'])
        for n in self.G.successors(node):
            attr = self.G.edge[node][n]
            nPoint = (self.G.node[n]['lat'], self.G.node[n]['lon'])
            intersection[n] = {'beginning': True, 'lanes':
                               attr.get('lanes', 1), 'bearing':
                               self.compassBearing(nodePoint, nPoint),
                               'oneway': self.isOneway(attr), 'forward':
                               attr.get('lanes:forward', 1), 'backward':
                               attr.get('lanes:backward', 1)}
        for n in self.G.predecessors(node):
            attr = self.G.edge[n][node]
            nPoint = (self.G.node[n]['lat'], self.G.node[n]['lon'])
            intersection[n] = {'beginning': False, 'lanes':
                               attr.get('lanes', 1), 'bearing':
                               self.compassBearing(nodePoint, nPoint),
                               'oneway': self.isOneway(attr), 'forward':
                               attr.get('lanes:forward', 1), 'backward':
                               attr.get('lanes:backward', 1)}
        return intersection

    def getIntersections(self, startNode):
        """ Use depth-first search to map intersection nodes and lane widths.
            Input: graph, startNode
            Output: dictionary mapping of intersection nodes
        """
        intersections = {}
        for fromN, toN in nx.dfs_edges(self.G, source=startNode):
            if self.isIntersection(toN):
                intersections[toN] = self.getIntersection(toN)
        return intersections

    def calcCrossSection(self, attr, bearing, clockwise=True):
        """ Calculate the parallel offsets for two-way and one-way links
            adjacent to the subject approach link in order to offsets to
            offset the subject link's endpoints.
            Input: intersection attribute, bearing, direction of cross street.
            Output: Adjusted endpoint offset distance
        """
        if attr['oneway']:
            return round(abs(int(attr['lanes']) * self.v.defaultWidth *
                             math.sin(math.radians(bearing))) / 2.0, 1)
        else:
            if clockwise:
                if attr['beginning']:
                    lane = 'backward'
                else:
                    lane = 'forward'
            else:
                if attr['beginning']:
                    lane = 'forward'
                else:
                    lane = 'backward'
            return round(abs(int(attr[lane]) * self.v.defaultWidth *
                             math.sin(math.radians(bearing))), 1)

    def getCrossStreets(self, intN, fromN):
        """ Get cross street lane width information.
            Input: node pairs approaching intersection
            Output: cross section information
        """
        intersection = self.intersections[intN]
        startBearing = intersection[fromN]['bearing']
        minBearing, maxBearing = -180, 180
        left, right = None, None
        for n, attr in intersection.items():
            diff = ((((startBearing-attr['bearing']) % 360)+540) % 360) - 180
            if (diff > 0 and diff < maxBearing):
                    left = n
                    maxBearing = diff
            elif (diff < 0 and diff > minBearing):
                    right = n
                    minBearing = diff
        if left:
            leftLane = self.calcCrossSection(intersection[left], maxBearing,
                                             clockwise=False)
        else:
            leftLane = 0
        if right:
            rightLane = self.calcCrossSection(intersection[right], minBearing)
        else:
            rightLane = 0
        return max([leftLane, rightLane])

    def createIntersectionDict(self):
        """ Create a dictionary for each link with centerline values and link
            attributes.
        """
        intersections = {}
        startNodes = self.getStartNodes()
        for n in startNodes:
            intersections.update(self.getIntersections(n))
        return intersections

    def getLink(self, nodes, attr, links):
        """ Get link attributes and points.
            Input: coordinate list and attribute dictionary
            Output: link dictionary
        """
        nodes = list(OrderedDict.fromkeys([n for n in nodes]))
        if self.isOneway(attr):
            wayID = attr['id']
            links[wayID] = {'forward': True, 'nodes': nodes, 'attr': attr}
        else:
            wayID = attr['id'] + '-F'
            links[wayID] = {'forward': True, 'nodes': nodes, 'attr': attr}
            wayID = attr['id'] + '-B'
            links[wayID] = {'forward': False, 'nodes': list(reversed(nodes)),
                            'attr': attr}

    def getLinks(self, startNode):
        """ Begin with startNode and end at an intersection
            Input: graph, startNode
            Output: nodes that comprise a single link
        """
        links = {}
        nodes = []
        prevAttr = None
        currAttr = None
        for fromN, toN in nx.dfs_edges(self.G, source=startNode):
            currAttr = self.G.edge[fromN][toN]
            if (self.isNewWay(fromN, toN, prevAttr) or
                    self.isIntersection(fromN)):
                self.getLink(nodes, prevAttr, links)
                nodes = []
            nodes.append(fromN)
            nodes.append(toN)
            prevAttr = currAttr
        self.getLink(nodes, currAttr, links)
        return links

    def offsetParallel(self, points, distance, clockwise=True):
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

    def offsetEndpoint(self, points, distance, beginning=True):
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
        assert math.sqrt(sum((b-a)**2)) > distance, ('distance exceeds node '
                                                     'pair length')
        db = (b-a)/np.linalg.norm(b-a)*distance
        return b-db

    def getTurnLanes(self, attr, direction='forward'):
        """ Parse turn lane info.
            Input: link attribute
            Output: turn lane instructions
        """
        if self.isOneway(attr):
            if 'turn:lanes' in attr:
                turns = attr['turn:lanes'].split('|')
            elif 'lanes' in attr:
                lanes = int(attr['lanes'])
                turns = ['through'] * lanes
        else:
            if 'turn:lanes:' + direction in attr:
                turns = attr['turn:lanes:' + direction].split('|')
            elif 'lanes:' + direction in attr:
                lanes = int(attr['lanes:' + direction])
                turns = ['through'] * lanes
        return [i.split(';') for i in turns]

    def nodesToXY(self, attr):
        """ Process links dictionary to calculate proper XY coordinates.
            Input: links dictionary
            Output: updated links dictionary with xy dictionary
        """
        nodes = attr['nodes']
        point3D = attr['point3D'] = [self.nodeToScaledMeters(n) for n in nodes]
        # Endpoints
        if nodes[0] in self.intersections:
            dist = self.getCrossStreets(nodes[0], nodes[1])
            point3D[0] = self.offsetEndpoint(point3D, dist)
        if nodes[-1] in self.intersections:
            dist = self.getCrossStreets(nodes[-1], nodes[-2])
            point3D[-1] = self.offsetEndpoint(point3D, dist, beginning=False)
        # Parallel
        if not self.isOneway(attr):
            dist = (sum(self.getLanes(attr)) * self.v.defaultWidth) / 2.0 / 2.0
            point3D = self.offsetParallel(point3D, dist)
        attr['point3D'] = [self.stringify(i) for i in point3D]
        # Lane number
        if self.isOneway(attr['attr']):
            attr['laneNumber'] = self.getLanes(attr)[0]
        elif attr['forward']:
            attr['laneNumber'] = self.getLanes(attr)[0]
        elif not attr['forward']:
            attr['laneNumber'] = self.getLanes(attr)[1]
        return attr

    def createLinkDict(self):
        """ Create a dictionary for each link with centerline values and link
            attributes.
        """
        links = {}
        startNodes = self.getStartNodes()
        for n in startNodes:
            links.update(self.getLinks(n))
        for k, attr in links.items():
            links[k] = self.nodesToXY(attr)
        return links

    def importLinks(self):
        """ Create links based on link dictionary, using attributes and
            centerlines as a guide.
            Input: link attributes and centerlines
            Output: returns vissim object with added links
        """
        for key, value in self.xy.items():
            attr = value['attr']
            point3D = value['point3D']
            lanes = int(value['laneNumber']) * [self.v.defaultWidth]
            self.v.links.createLink(**{'point3D': point3D, 'lane': lanes,
                                       'name': attr['id']})

    def drawLinks(self, links):
        """ Plot links for viewing
        """
        from matplotlib.pyplot import plot
        for i in links.keys():
            plot([j[0] for j in links[i]], [j[1] for j in links[i]])
