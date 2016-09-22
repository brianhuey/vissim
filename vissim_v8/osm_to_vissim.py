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
        self.ways = self.createWaysDict()
        self.xy = self.createXYDict()
        self.v.createReference(self.refX, self.refY)

    def getWayByNode(self, fromN, toN):
        try:
            fwd = self.G.edge[fromN][toN]
            wayID = fwd['id']
            if wayID in self.ways.keys():
                return wayID
            else:
                return wayID + '-F'
        except:
            bkd = self.G.edge[toN][fromN]
            return bkd['id'] + '-B'

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
        """ If a node has only one successor node and no predecessors, then
            it's at the exterior of the model and pointing in the correct
            direction.
        """
        if len(self.G.successors(n)) == 1 and len(self.G.predecessors(n)) == 0:
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

    def calcCrossSection(self, intN, fromN, bearing, clockwise=True):
        """ Calculate the parallel offsets for two-way and one-way links
            adjacent to the subject approach link in order to offsets to
            offset the subject link's endpoints.
            Input: intersection attribute, bearing, direction of cross street.
            Output: Adjusted endpoint offset distance
        """
        attr = self.intersections[intN][fromN]
        if attr['oneway']:
            return round(abs(int(attr['lanes']) * self.v.defaultWidth *
                             math.sin(math.radians(bearing))) / 2.0, 1)
        else:
            if clockwise:
                if attr['beginning']:
                    # way is pointing away from the intersection
                    lane = 'backward'
                    wayID = self.getWayByNode(fromN, intN)
                else:
                    # way is pointing toward the intersection
                    lane = 'forward'
                    wayID = self.getWayByNode(intN, fromN)
            else:
                if attr['beginning']:
                    lane = 'forward'
                    wayID = self.getWayByNode(intN, fromN)
                else:
                    lane = 'backward'
                    wayID = self.getWayByNode(fromN, intN)
            offset = float(self.ways[wayID]['offset'])
            offset += int(attr[lane]) / 2.0
            return round(abs(offset * self.v.defaultWidth *
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
            leftLane = self.calcCrossSection(intN, left, maxBearing,
                                             clockwise=False)
        else:
            leftLane = 0
        if right:
            rightLane = self.calcCrossSection(intN, right, minBearing)
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

    def getTurnLanes(self, attr, direction='forward'):
        """ Parse turn lane info.
            Input: link attribute
            Output: turn lane instructions
        """
        attr = attr['attr']
        if self.isOneway(attr):
            if 'turn:lanes' in attr:
                turns = attr['turn:lanes'].split('|')
            elif 'lanes' in attr:
                lanes = int(attr['lanes'])
                turns = ['through'] * lanes
            else:
                turns = ['through']
        else:
            if 'turn:lanes:' + direction in attr:
                turns = attr['turn:lanes:' + direction].split('|')
            elif 'lanes:' + direction in attr:
                lanes = int(attr['lanes:' + direction])
                turns = ['through'] * lanes
            elif 'lanes' in attr:
                lanes = int(attr['lanes']) / 2
                turns = ['through'] * lanes
            else:
                turns = ['through']
        turns = ['through' if i == '' or i.lower() == 'none' else i for i in
                 turns]
        return [i.split(';') for i in turns]

    def calcLaneAlignment(self, waysDict):
        """ For a list of ways between two intersections, calculate the
            correct lane transitions as offsets from the centerline.
            Input: dict of ways
            Output: modified dict with offsets
        """
        aFwdAttr = waysDict['forward'].values()[0]
        aBkdAttr = waysDict['backward'].values()[0]
        aFwdLanes, aBkdLanes = self.getLanes(aFwdAttr)
        bFwdAttr = waysDict['forward'].values()[-1]
        bBkdAttr = waysDict['backward'].values()[-1]
        bFwdLanes, bBkdLanes = self.getLanes(bFwdAttr)
        aLanes, bLanes = aFwdLanes + aBkdLanes, bFwdLanes + bBkdLanes
        aDiff, bDiff = aFwdLanes - aBkdLanes, bFwdLanes - bBkdLanes
        # Calculate the offsets for the (A/B) ways: those that connect to an
        # intersection
        if aLanes == bLanes:
            aFwdAttr['offset'] = aFwdLanes / 2.0 - (aDiff / 2.0)
            aBkdAttr['offset'] = aBkdLanes / 2.0 + (aDiff / 2.0)
            bFwdAttr['offset'] = bFwdLanes / 2.0 - (bDiff / 2.0)
            bBkdAttr['offset'] = bBkdLanes / 2.0 + (bDiff / 2.0)
        elif aLanes > bLanes:
            aFwdAttr['offset'] = aFwdLanes / 2.0 - (aDiff / 2.0)
            aBkdAttr['offset'] = aBkdLanes / 2.0 + (aDiff / 2.0)
            bFwdAttr['offset'] = aFwdLanes / 2.0 - (aDiff / 2.0)
            aBkdTurns = self.getTurnLanes(aBkdAttr, direction='backward')
            lefts = sum([1 if i == ['left'] else 0 for i in aBkdTurns])
            bBkdAttr['offset'] = bBkdLanes / 2.0 + (bDiff / 2.0) + lefts / 2.0
        elif aLanes < bLanes:
            bFwdAttr['offset'] = bFwdLanes / 2.0 - (bDiff / 2.0)
            bBkdAttr['offset'] = bBkdLanes / 2.0 + (bDiff / 2.0)
            aBkdAttr['offset'] = bBkdLanes / 2.0 + (bDiff / 2.0)
            bFwdTurns = self.getTurnLanes(bFwdAttr)
            lefts = sum([1 if i == ['left'] else 0 for i in bFwdTurns])
            aFwdAttr['offset'] = aFwdLanes / 2.0 + (aDiff / 2.0) + lefts / 2.0
        # Calculate the offsets for the intermediate ways: those that don't
        # connect to an intersection.
        if len(waysDict['forward']) > 2:
            fwdOffset = bBkdAttr['offset']
            bkdOffset = aFwdAttr['offset']
            fwdAttrs = waysDict['forward'].values()[1:-1]
            bkdAttrs = waysDict['backward'].values()[1:-1]
            for attr in fwdAttrs:
                attr['offset'] = fwdOffset
            for attr in bkdAttrs:
                attr['offset'] = bkdOffset
        fwd = {k + '-F': v for k, v in waysDict['forward'].items()}
        bkd = {k + '-B': v for k, v in waysDict['backward'].items()}
        return dict(fwd, **bkd)

    def getWay(self, ways):
        """ Get way attributes and points.
            Input: coordinate list and attribute dictionary
            Output: way dictionary
        """
        waysDict = OrderedDict()
        for way in ways:
            way = list(OrderedDict.fromkeys([n for n in way]))
            fromN = way[0]
            toN = way[1]
            attr = self.G.edge[fromN][toN]
            if self.isOneway(attr):
                if not waysDict.get('oneway'):
                    waysDict['oneway'] = OrderedDict()
                wayID = attr['id']
                waysDict['oneway'][wayID] = {'forward': True, 'nodes': way,
                                             'attr': attr, 'offset': 0}
            else:
                wayID = attr['id']
                if (not waysDict.get('forward') and
                        not waysDict.get('backward')):
                    waysDict['forward'] = OrderedDict()
                    waysDict['backward'] = OrderedDict()
                waysDict['forward'][wayID] = {'forward': True, 'nodes': way,
                                              'attr': attr}
                waysDict['backward'][wayID] = {'forward': False, 'nodes':
                                               list(reversed(way)), 'attr':
                                               attr}
        if waysDict.get('forward') and waysDict.get('oneway'):
            fwdBkd = self.calcLaneAlignment(waysDict)
            return dict(fwdBkd, **waysDict['onway'])
        elif waysDict.get('forward'):
            return self.calcLaneAlignment(waysDict)
        elif waysDict.get('oneway'):
            return waysDict['oneway']

    def getWays(self, startNode):
        """ Begin with startNode and traverse the graph, collecting the nodes
            of each way. When a new way is encountered, start a new list of
            nodes. When a new intersection is encountered, pass the list of
            ways to the getWay function for processing.
            Input: graph, startNode
            Output: dictionary used for creating VISSIM links
        """
        waysDict = {}
        ways = []
        nodes = []
        prevAttr = None
        currAttr = None
        for fromN, toN in nx.dfs_edges(self.G, source=startNode):
            currAttr = self.G.edge[fromN][toN]
            if self.isIntersection(fromN):
                ways.append(nodes)
                waysDict.update(self.getWay(ways))
                ways = []
                nodes = []
            elif self.isNewWay(fromN, toN, prevAttr):
                ways.append(nodes)
                nodes = []
            nodes.append(fromN)
            nodes.append(toN)
            prevAttr = currAttr
            if self.isExterior(toN):
                ways.append(nodes)
                self.getWay(ways)
        ways.append(nodes)
        waysDict.update(self.getWay(ways))
        return waysDict

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
        if math.sqrt(sum((b-a)**2)) < distance:
            distance = math.sqrt(sum((b-a)**2)) * 0.99
        db = (b-a) / np.linalg.norm(b-a) * distance
        return b - db

    def nodesToXY(self, attr):
        """ Process links dictionary to calculate proper XY coordinates.
            Input: links dictionary
            Output: updated links dictionary with xy dictionary
        """
        width = self.v.defaultWidth
        nodes = attr['nodes']
        point3D = attr['point3D'] = [self.nodeToScaledMeters(n) for n in nodes]
        # Parallel
        if not self.isOneway(attr):
            dist = attr['offset'] * width
            point3D = self.offsetParallel(point3D, dist)
        # Endpoints
        if nodes[0] in self.intersections:
            dist = self.getCrossStreets(nodes[0], nodes[1])
            point3D[0] = self.offsetEndpoint(point3D, dist)
        if nodes[-1] in self.intersections:
            dist = self.getCrossStreets(nodes[-1], nodes[-2])
            point3D[-1] = self.offsetEndpoint(point3D, dist, beginning=False)
        attr['point3D'] = [self.stringify(i) for i in point3D]
        # Lane number
        if self.isOneway(attr['attr']):
            attr['laneNumber'] = self.getLanes(attr)[0]
        elif attr['forward']:
            attr['laneNumber'] = self.getLanes(attr)[0]
        elif not attr['forward']:
            attr['laneNumber'] = self.getLanes(attr)[1]
        return attr

    def createWaysDict(self):
        """ Create a dictionary for each way calculating lane alignment
            parameters and directionality.
        """
        ways = {}
        startNodes = self.getStartNodes()
        for n in startNodes:
            ways.update(self.getWays(n))
        return ways

    def createXYDict(self):
        """ Create a dictionary for each way calculating node locations in
            XY space, compass bearing and intersection offsets.
        """
        xy = {}
        for k, attr in self.ways.items():
            xy[k] = self.nodesToXY(attr)
        return xy

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
            self.v.Links.createLink(**{'point3D': point3D, 'lane': lanes,
                                       'name': attr['id']})

    def drawLinks(self, links):
        """ Plot links for viewing
        """
        from matplotlib.pyplot import plot
        for i in links.keys():
            plot([j[0] for j in links[i]], [j[1] for j in links[i]])
