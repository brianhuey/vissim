#!/usr/bin/env python
# OSM to VISSIM converter
from vissim_objs import Vissim
import networkx as nx
from osm_to_graph import read_osm
from osm_to_graph import BusStopNode
from collections import OrderedDict
import geo_math as geo
import math
import vissim_v8 as vissim
import matplotlib.pyplot as plt
import numpy as np
import sys
import pickle


#my added
osmFile = "map.osm"

highway_cat = 'motorway|trunk|primary|secondary|tertiary|road|residential|service|motorway_link|trunk_link|primary_link|secondary_link|teriary_ilnk'




def stringify(iterable):
    """ Convert tuple containing numbers to string
        Input: iterable with numbers as values
        Output: tuple with strings as values
    """
    return tuple([str(i) for i in iterable])
                                                                                
                                                                                
 
class OSM(Vissim):
    def __init__(self, osmFile ):

        self.includeBusStops = '--include-bus-stops' in sys.argv  #RV
        self.G, self.osm = read_osm(osmFile)
	#RV
	c = 0
    	for n in self.osm.nodes:
		if (type(self.osm.nodes[n]) is BusStopNode):
			c += 1
		pass
	pass
	print "Number of bs nodes is %d" %(c)
        self.v = Vissim()
        self.roadTypes = ['motorway', 'motorway_link', 'primary', 'secondary',
                          'tertiary', 'traffic_signals', 'bus_stop']
        self.refLat, self.refLng = self.getRefLatLng()
        self.refX, self.refY = self.latLngToMeters(self.refLat, self.refLng)
        self.intersections = self.createIntersectionDict()
        self.ways = self.createWaysDict()
	if ( "--loadXYDict" not in sys.argv):
        	self.xy = self.createXYDict()
		fh = open('xydict.pickle','wb')
		pickle.dump(self.xy,open('xydict.pickle','wb'))
		fh.close()
	else:
		self.xy = pickle.load(open('xydict.pickle','r'))

	#RV 
	self.importLinks()
        if ( self.includeBusStops == True):
		self.processBusStops()
	self.importConnectors()
        
        
        self.v.createReference(self.refX, self.refY)
        self.v.export("testxml.inpx")

        
        
        '''
        plt.ylim(-1.0, 1.0);
        x = np.linspace(0, 10, 1000)
        plt.plot(x, 2*np.sin(x*5));
        plt.show()        
        '''


    # Create reference point
    def getRefLatLng(self):
        """ Get reference lat/lng for xy conversion.
            Input: Graph
            Output: lat, long tuple
        """
        latlng = self.G.node.itervalues().next()
        return latlng['lat'], latlng['lon']

    # Boolean helper functions
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

    # Get start nodes and lane info for creating intersection and ways dicts
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
            for prev, n in nx.edge_dfs(self.G, source=node):
                if n in edgeNodes:
                    edgeNodes.remove(n)
        return edgeNodes

    # Intersection dict
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
            if attr['highway'] not in self.roadTypes:
                continue
            nPoint = (self.G.node[n]['lat'], self.G.node[n]['lon'])
            intersection[n] = {'beginning': True, 'lanes':
                               attr.get('lanes', 1), 'bearing':
                               self.compassBearing(nodePoint, nPoint),
                               'oneway': self.isOneway(attr), 'forward':
                               attr.get('lanes:forward', 1), 'backward':
                               attr.get('lanes:backward', 1)}
        for n in self.G.predecessors(node):
            attr = self.G.edge[n][node]
            if attr['highway'] not in self.roadTypes:
                continue
            nPoint = (self.G.node[n]['lat'], self.G.node[n]['lon'])
            intersection[n] = {'beginning': False, 'lanes':
                               attr.get('lanes', 1), 'bearing':
                               self.compassBearing(nodePoint, nPoint),
                               'oneway': self.isOneway(attr), 'forward':
                               attr.get('lanes:forward', 1), 'backward':
                               attr.get('lanes:backward', 1)}
        return intersection

    def createIntersectionDict(self):
        """ Use depth-first search to map intersection nodes and lane widths.
            Input: graph, startNode
            Output: dictionary mapping of intersection nodes
        """
        intersections = {}
        for fromN, toN in nx.edge_dfs(self.G):
            if self.isIntersection(toN):
		print 'Processing intersection %d' %(int(toN))
                intersections[toN] = self.getIntersection(toN)
        return intersections

    # Ways dict
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

    def getLanes(self, attr):
        """ Determine number of lanes based on OSM attributes.
            Input: OSM attribute
            Output: tuple with number of lanes (forward, backward),
                    False if no lane numbers specified
        """
        if self.isOneway(attr['attr']):
            return len(self.getTurnLanes(attr)), 0
        else:
            forward = len(self.getTurnLanes(attr))
            backward = len(self.getTurnLanes(attr, direction='backward'))
            return forward, backward

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
        if ways == [[]]:
            return waysDict
        for way in ways:
            way = list(OrderedDict.fromkeys([n for n in way]))
            fromN = way[0]
            toN = way[1]
            attr = self.G.edge[fromN][toN]
            fwdLanes, bkdLanes = self.getLanes({'attr': attr})
            if self.isOneway(attr):
                if not waysDict.get('oneway'):
                    waysDict['oneway'] = OrderedDict()
                wayID = attr['id']
                waysDict['oneway'][wayID] = {'forward': True, 'nodes': way,
                                             'attr': attr, 'offset': 0,
                                             'laneNumber': fwdLanes}
            else:
                wayID = attr['id']
                if (not waysDict.get('forward') and
                        not waysDict.get('backward')):
                    waysDict['forward'] = OrderedDict()
                    waysDict['backward'] = OrderedDict()
                waysDict['forward'][wayID] = {'forward': True, 'nodes': way,
                                              'attr': attr, 'laneNumber':
                                              fwdLanes}
                waysDict['backward'][wayID] = {'forward': False, 'nodes':
                                               list(reversed(way)), 'attr':
                                               attr, 'laneNumber': bkdLanes}
        if waysDict.get('forward') and waysDict.get('oneway'):
            fwdBkd = self.calcLaneAlignment(waysDict)
            return dict(fwdBkd, **waysDict['oneway'])
        elif waysDict.get('forward'):
            return self.calcLaneAlignment(waysDict)
        elif waysDict.get('oneway'):
            return waysDict['oneway']

    def createWaysDict(self):
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
        
        for fromN, toN in nx.edge_dfs(self.G):
            currAttr = self.G.edge[fromN][toN]
            print 'createWaysDict : fromN %s toN %s ' %(fromN,toN)
            #print currAttr['highway']
            if currAttr['highway'] not in self.roadTypes:
                continue
            if self.isIntersection(fromN):
                ways.append(nodes)
#                print ways
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

    # XY dict - translate nodes from ways dict to X,Y points including lane
    # offsets

    def getWayByNode(self, fromN, toN):
        if (fromN, toN) in self.G.edges():
            # Forward way
            wayID = self.G.edge[fromN][toN]['id']
            if wayID in self.ways.keys():
                return wayID
            elif wayID + '-F' in self.ways.keys():
                return wayID + '-F'
            else:
                raise KeyError
        elif (toN, fromN) in self.G.edges():
            # Backward way
            wayID = self.G.edge[toN][fromN]['id'] + '-B'
            if wayID in self.ways.keys():
                return wayID
            else:
                raise KeyError
        else:
            raise KeyError

    '''
	RV Encodes the link id for vissim based on wayID used in this script
	Input : wayID e.g typical syntax : '175878996-2' 
	Output : link ID in vissim syntax  e.g.  u'17587899602'
    '''
    def wayIDToVissimLinkNumber(self,wayID):
	    tmp = wayID
	    tmp2 = tmp.replace('-','0',1)
	    tmp3 = tmp2.split('-')
	    return(tmp3[0])

    '''
	RV Encodes wayID used in this script from the vissim link id
	Input : link ID in vissim syntax  e.g.  u'17587899602'
	Output : wayID e.g typical syntax : e.g typical syntax : '175878996-2' 
    '''
    def vissimLinkNumberToWayID(self,vlinkID):
	#todo
        pass


    '''
	RV Returns all the way ids with the specified name
    '''
    def getWayByName(self, name):
	wByN = []
	for w in self.ways:
		#print self.ways[w]['attr']['name']
		try:
		   if( self.ways[w]['attr']['name'] == name):
			wByN.append( w )
		except:
			#print 'Warning : way %s has no name' %(w)
			wByN.append( w )
			continue;
		pass
	pass
	return wByN
    pass

    '''
	RV Gets the way nearest to the given lat,lon
    '''
    def getNearestLinks(self, btNum, wayList, latlon):
	p1 = latlon
        BusStopPoint3D = self.latLngToScaledMeters(p1[0], p1[1])
	p2 = latlon
	offset = 0.0
	nw = wayList[0]
	validLinksDict = {}
	curr = []
	validLinksDict[btNum] = curr
	for w in wayList:
	    print 'processing way %s with %d nodes ' %(w, len(self.ways[w]['nodes']))
	    linkAttr = {}
	    linkAttr['wayID'] = w
	    OriginOfWayPoint3D = self.ways[w]['point3D'][0]
	    EndOfWayPoint3D = self.ways[w]['point3D'][-1]
	    linkAttr['linkLength'] = geo.getDistance(OriginOfWayPoint3D,EndOfWayPoint3D)
	    # len should be at least 2
	    tmpSegList = []
	    for i in range(len(self.ways[w]['nodes'])-1 ):
	        node1Point3D = self.ways[w]['point3D'][i]
	    	node2Point3D = self.ways[w]['point3D'][i+1]
	        nwl = geo.getDistance(node1Point3D,node2Point3D)
	    	#print 'processing segment of way %s with len  %f ' %(w, nwl)
	    
	    	BSPointOnWay = geo.getNearestPointOnSegment(BusStopPoint3D, (node1Point3D, node2Point3D))
	    	if (BSPointOnWay == None ):
			#print '+++ Nearest point not on segment ; Skipping way %s' %(w)
			continue;
	    	pass
		# else valid perp to Bus stop found on segment
		newpd = geo.getDistance(BusStopPoint3D,BSPointOnWay)
	    	linkAttr['PerpDistance'] = newpd
	        linkAttr['BusStopPoint'] = BSPointOnWay
	    	linkAttr['DistanceToOrigin'] = geo.getDistance(BusStopPoint3D,OriginOfWayPoint3D)
	        linkAttr['DistanceToEnd'] = geo.getDistance(BusStopPoint3D,EndOfWayPoint3D)
	        linkAttr['Offset'] = geo.getDistance(BSPointOnWay, OriginOfWayPoint3D) 
		tmpSegList.append(linkAttr)
	    pass
	    if (len(tmpSegList) == 0):
		continue;	
	    
	    vls = sorted(tmpSegList,key=lambda k:k['PerpDistance'])
	    curr = validLinksDict[btNum]
	    try:
	    	curr.append ( vls[0])
	    	validLinksDict[btNum] = curr 
	    except:
	    	print '*** Failed to add item to valid links Dictionary'
	pass
	return validLinksDict



    '''
	RV Gets the nearest link 
	todo : add checks - link segment which can fit the bus stop in it
    '''
    def selectNearest(self, validLinks ):
	#print 'Processing %d links ' %(len(validLinks))
	if (len(validLinks) <=0 ):
		print 'Empty list of links'
		return None
	pass
	vls = sorted(validLinks,key=lambda k:k['PerpDistance'])
	# add check here - perpDistance should not be more than 10m >

	linkAttr = vls[0]
	newd1 = linkAttr['DistanceToOrigin'] 
	if ( (newd1 + 20.0) > linkAttr['linkLength']): # since cannot accomodate start of busstop ?
		print '+++Warning : may need to skip  link %s ; since too short?' %(linkAttr['wayID'])
    	return linkAttr
    pass

    def calcTurn(self, startBearing, endBearing):
        thruMin, thruMax = 135, -135
        leftMin, leftMax = -135, -45
        rightMin, rightMax = 45, 135
        left, right, through = None, None, None
        diff = ((((startBearing-endBearing) % 360)+540) % 360) - 180
        if diff >= thruMin or diff <= thruMax:
            return 'through'
        elif diff > leftMin and diff < leftMax:
            return 'left'
        elif diff > rightMin and diff < rightMax:
            return 'right'
        else:
            return None

    def calcTurns(self, intN, fromN):
        """ For a given approach to an intersection, find the wayIDs
            which represent left, through and right turns. In the case where
            a way ends mid-block, then specify the next way to connect to.
            Input: intersection node, from node
            Output: Dict of wayIDs and turn movements
        """
        turns = {'left': [], 'right': [], 'through': []}
	try:
		way1 = self.getWayByNode(fromN,intN)
        	way1Attr = self.ways[way1]
                way1TurnLanes = self.getTurnLanes(way1Attr)
	except:
		way1Turns = {}
        if intN in self.intersections:
            intersection = self.intersections[intN]
            startBearing = intersection[fromN]['bearing']
            for n, attr in intersection.items():
                endBearing = attr['bearing']
                try:
                    wayID = self.getWayByNode(intN, n)
        	    wayIDAttr = self.ways[wayID]
                    wayIDTurnLanes = self.getTurnLanes(wayIDAttr)

                    turn = self.calcTurn(startBearing, endBearing)
                    turns[turn].append(wayID)
		    #RV 
		    # handle case where wayID is a little piece of the same
		    # way as way1 but should have been ideally fused into one
		    # way
		    # if wayID is having a right turn, add that id also.
		    # if wayID is having a left turn, add that id also.
		    if (turn == 'through'):
		    	if self.hasTurn(wayIDTurnLanes, 'right') and self.hasTurn(way1TurnLanes,'right'):
				turns['right'].append(wayID)
		    	if self.hasTurn(wayIDTurnLanes, 'left') and self.hasTurn(way1TurnLanes,'left'):
				turns['left'].append(wayID)
		    

                except:
                    continue
        else:
            if (fromN in self.G.successors(intN) and
                    len(self.G.predecessors(intN)) == 1):
                n = self.G.predecessors(intN)[0]
                try:
                    wayID = self.getWayByNode(intN, n)
                    turns['through'].append(wayID)
                except:
                    pass
            elif (fromN in self.G.predecessors(intN) and
                    len(self.G.successors(intN)) == 1):
                n = self.G.successors(intN)[0]
                try:
                    wayID = self.getWayByNode(intN, n)
                    turns['through'].append(wayID)
                except:
                    pass
        return turns

    def calcCrossSection(self, intN, fromN, bearing, clockwise=True):
        """ Calculate the parallel offsets for two-way and one-way links
            adjacent to the subject approach link in order to offsets to
            offset the subject link's endpoints.
            Input: intersection attribute, bearing, direction of cross street.
            Output: Adjusted endpoint offset distance
        """
        attr = self.intersections[intN][fromN]
        if attr['oneway']:
            return round(abs(int(attr['lanes']) *
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
            return round(abs(offset * math.sin(math.radians(bearing))), 1)

    def getCrossStreets(self, intN, fromN):
        """ Get cross street lane width information.
            Input: node pairs approaching intersection
            Output: cross section information
        """
        intersection = self.intersections[intN]
        startBearing = intersection[fromN]['bearing']
        minBearing, maxBearing = None, None
        left, right = None, None
        for n, attr in intersection.items():
            endBearing = attr['bearing']
            diff = ((((startBearing-endBearing) % 360)+540) % 360) - 180
            if self.calcTurn(startBearing, endBearing) == 'left':
                left = n
                maxBearing = diff
            elif self.calcTurn(startBearing, endBearing) == 'right':
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

    def latLngToScaledMeters(self, lat, lng):
        x, y = self.latLngToMeters(lat, lng)
        scale = 1 / math.cos(math.radians(self.refLat))
        scaleX = (x - self.refX) / scale
        scaleY = (y - self.refY) / scale
        return (scaleX, scaleY, 0)

    def getLatLng(self, n):
        """ Return lat/lng tuple for a given node.
        """
        return self.G.node[n]['lat'], self.G.node[n]['lon']

    def nodeToScaledMeters(self, n):
        """ Apply Mercator scaling factor based on latitude to xy points.
            Input: node
            Output: correctly scaled xy
        """
        lat, lng = self.getLatLng(n)
        x, y = self.latLngToMeters(lat, lng)
        scale = 1 / math.cos(math.radians(self.refLat))
        scaleX = (x - self.refX) / scale
        scaleY = (y - self.refY) / scale
        return (scaleX, scaleY, 0)

    def nodesToXY(self, attr):
        """ Process links dictionary to calculate proper XY coordinates.
            Input: links dictionary
            Output: updated links dictionary with xy dictionary
        """
        width = self.v.defaultWidth
        nodes = attr['nodes']
        #print "#######", nodes		
        point3D = attr['point3D'] = [self.nodeToScaledMeters(n) for n in nodes]
        #print point3D  		
        		
        # Parallel
        if not self.isOneway(attr):
            dist = attr['offset'] * width
            #print "###", point3D			
            #print nodes
            #tt = geo.offsetEndpoint(point3D, 1.0)
            #print tt
            #print "@@@", point3D
            '''tt = [[468.514244231,48.6922583583,0],
                  [468.069585906,89.8343879775,0],
                  [476.929403034,136.402838403,0]]
			'''	  
            point3D = geo.offsetParallel(point3D, dist)			
            #point3D = geo.offsetParallel(point3D, dist)
        # Endpoints / Turns
        if nodes[0] in self.intersections:
            dist = self.getCrossStreets(nodes[0], nodes[1]) * width
            point3D[0] = geo.offsetEndpoint(point3D, dist)
        if nodes[-1] in self.intersections:
            dist = self.getCrossStreets(nodes[-1], nodes[-2]) * width
            point3D[-1] = geo.offsetEndpoint(point3D, dist, beginning=False)
        # Turn dictionary only for ways pointing toward the intersection
        attr['turns'] = self.calcTurns(nodes[-1], nodes[-2])
        attr['point3D'] = [stringify(i) for i in point3D]
        return attr

    def createXYDict(self):
        """ Create a dictionary for each way calculating node locations in
            XY space, compass bearing and intersection offsets.
        """
        xy = {}
        for k, attr in self.ways.items():
            #print self.ways		
	    #RV extract the relevant parts of the way id without the -B/-F encoding
	    tmp = k
	    if (k.endswith('-B') or k.endswith('-F')):
	    	tmp3 = tmp.split('-')
	    	tmp = tmp3[0] + '-' + tmp3[1]
            print 'XY>>  Way being processed %s ' %(tmp)
            xy[tmp] = self.nodesToXY(attr)
        return xy

    # Create VISSM objects from OSM
    def importLinks(self):
        """ Create links based on xy dictionary, using attributes and
            centerlines as a guide.
            Input: xy dictionary
            Output: modifies vissim object in place
        """
        for wayID, attr in self.xy.items():
            point3D = attr['point3D']
            lanes = int(attr['laneNumber']) * [self.v.defaultWidth]
	    tmp = self.wayIDToVissimLinkNumber(wayID)
	    try:
            	self.v.Links.createLink(**{'point3D': point3D, 'lane': lanes,
                                       'no': tmp})
	    except:
		print 'Could not create link for %s' %(tmp)
		continue
	pass
    pass

    def hasTurn(self, turnLanes, turn):
        """ Check if a turning movement exists at an approach.
            Input: turnLanes, turn
            Output: bool
        """
        for lane in turnLanes:
            if turn in lane:
                return True
            else:
                continue
        return False

    def processTurns(self, fromLink, turnTo, turnLanes, turn):
        turns = sum([1 if turn in lane else 0 for lane in turnLanes])
        fromLane = min([i+1 if turn in v else '' for i, v in
                        enumerate(reversed(turnLanes))])
        for wayID in turnTo[turn]:
	    #RV
	    tmp = self.wayIDToVissimLinkNumber(wayID)
	    print 'Processing wayid old %s new %s' %(wayID, tmp)
	    try:
            	attr = self.v.Links._getAttributes('no', tmp)
                toLink = self.v.Links._getAttributes('no', tmp)['no']
                lanes = len(self.v.Links.getLanes(toLink))
	    except:
		print ' Attribute/lanes not found for way %s' %(tmp)
		continue
	    pass
            if lanes < turns:
                turns = lanes
            toLane = lanes - turns + 1
	    try:
            	self.v.Links.createConnector(fromLink, fromLane, toLink, toLane, turns)
	    except:
		print ' creat connector failed ' 
		continue
	    pass

    def importConnectors(self):
        """ Create connectors based on xy dictionary.
            Input: xy dictionary
            Output: modifies vissim object in place
        """
        for wayID, attr in self.xy.items():
            if 'turns' in attr:
                if wayID[-1] == 'B':
                    direction = 'backward'
                else:
                    direction = 'forward'
	    	#RV
	    	tmp = self.wayIDToVissimLinkNumber(wayID)
		print 'Processing wayid %s' %(tmp)
		try:
                	fromLink = self.v.Links._getAttributes('no', tmp)['no']
		except:
			print 'Discarding wayID %s' %(tmp)
			continue
		pass
                turnTo = attr['turns']
                turnLanes = self.getTurnLanes(attr, direction=direction)
                if len(turnTo['left']) > 0 and self.hasTurn(turnLanes, 'left'):
                    self.processTurns(fromLink, turnTo, turnLanes, 'left')
                if (len(turnTo['through']) > 0 and
                        self.hasTurn(turnLanes, 'through')):
                    self.processTurns(fromLink, turnTo, turnLanes, 'through')
                if (len(turnTo['right']) > 0 and
                        self.hasTurn(turnLanes, 'right')):
                    self.processTurns(fromLink, turnTo, turnLanes, 'right')

        
    def processBusStops(self):
	ptStops = []
    	for n in self.osm.nodes:
		if (type(self.osm.nodes[n]) is BusStopNode):
			try:
			    locName = self.osm.nodes[n].tags['location']
			except:
			    locName = ''
			try:
			    btNum = int(self.osm.nodes[n].tags['asset_ref'])
			except:
			    continue ; # skip bus stop without a bt number
			print 'NonWayNode found of type %s <%d> is at location %s' %(self.osm.nodes[n].typeTag, btNum, locName)
			wayList = []
			lat = self.osm.nodes[n].lat
			lon = self.osm.nodes[n].lon
			wayList = self.getWayByName(locName)
			if (len(wayList) != 0) :
				nearestLinks = self.getNearestLinks(btNum, wayList, (self.osm.nodes[n].lat, self.osm.nodes[n].lon))
				if (len(nearestLinks[btNum]) ==0 ):
				    continue
				nearestWay = self.selectNearest(nearestLinks[btNum])
				if (nearestWay == None):
					print 'No links for bus stop %d ' %(btNum)
					continue;
				pass
				print 'Nearest Way is %s <len %f> at distance %f m from BusStop' %(nearestWay['wayID'], nearestWay['linkLength'],nearestWay['PerpDistance'])
				#print 'Offset of bus-stop to start of link is %f meters' %(nearestWay['DistanceToOrigin'])
				pts = self.InitPTStop(btNum,nearestWay)
            			ptStops.append(pts)
			else:
				print 'No ways with name %s ' %(locName)
			pass
		pass
	pass

	print 'Processed Bus stops -- count = %d' %(len(ptStops))
        for i in range(len(ptStops)):
	    print ptStops[i]
            self.v.PTStop.createptStop(**ptStops[i])
	pass

	#RV --2018--Jan--
    pass

    def InitPTStop(self,btNum, wayInfo):

	ptStopRecord = {}
	ptStopRecord['no'] = btNum
	if (wayInfo['linkLength'] < 20):
    	    print ' Bus stop on v. short way'
	    ptStopRecord['length'] = wayInfo['linkLength'] 
	pass
	offset = wayInfo['DistanceToOrigin']
	if ((offset + 20) >= wayInfo['linkLength']):
		print ' Adjusting offset for Bus stop '
		offset = offset - 20.0;
		if (offset < 0.0): #RV No negative offsets
			offset = 0.0
	pass
	ptStopRecord['pos'] = offset 
	#RV : fix the lane number
	lanes = int(self.ways[wayInfo['wayID']]['laneNumber'])
	tmp = self.wayIDToVissimLinkNumber(wayInfo['wayID'])
	ptStopRecord['lane'] = tmp + ' ' + str(lanes)
	return ptStopRecord

#my added
if __name__ == '__main__':
	o=OSM(osmFile)

#o = OSM(osmFile)
