"""
Read graphs in Open Street Maps osm format
Based on osm.py from brianw's osmgeocode
http://github.com/brianw/osmgeocode, which is based on osm.py from
comes from Graphserver:
http://github.com/bmander/graphserver/tree/master and is copyright (c)
2007, Brandon Martin-Anderson under the BSD License
"""

from lxml import etree
import copy
import networkx

import sys

highway_cat = 'motorway|trunk|primary|secondary|tertiary|road|residential|service|motorway_link|trunk_link|primary_link|secondary_link|teriary_link'

#RV
gIncBusStop = '--include-bus-stops' in sys.argv

def download_osm(left,bottom,right,top,highway_cat):
    """
    Downloads OSM street (only highway-tagged) Data using a BBOX,
    plus a specification of highway tag values to use

    Parameters
    ----------
    left,bottom,right,top : BBOX of left,bottom,right,top coordinates in WGS84
    highway_cat : highway tag values to use, separated by pipes (|), for
    instance 'motorway|trunk|primary'

    Returns
    ----------
    stream object with osm xml data

    """
    # Return a filehandle to the downloaded data."""
    from urllib import urlopen
    # fp = urlopen( "http://api.openstreetmap.org/api/0.6/map?bbox=%f,%f,%f,%f"%(left,bottom,right,top) )
    # fp = urlopen( "http://www.overpass-api.de/api/xapi?way[highway=*][bbox=%f,%f,%f,%f]"%(left,bottom,right,top) )
    print "trying to download osm data from "+str(left),str(bottom),str(right),str(top)+" with highways of categories"+highway_cat
    try:
        print "downloading osm data from "+str(left),str(bottom),str(right),str(top)+" with highways of categories"+highway_cat
        fp = urlopen( "http://www.overpass-api.de/api/xapi?way[highway=%s][bbox=%f,%f,%f,%f]"%(highway_cat,left,bottom,right,top) )
        # slooww only ways,and in ways only "highways" (i.e. roads)
        # fp = urlopen( "http://open.mapquestapi.com/xapi/api/0.6/way
        # [highway=*][bbox=%f,%f,%f,%f]"%(left,bottom,right,top) )
        return fp
    except:
        print "osm data download unsuccessful"


def read_osm(filename_or_stream, only_roads=True):
    """Read graph in OSM format from file specified by name or by stream object.

    Parameters
    ----------
    filename_or_stream : filename or stream object

    Returns
    -------
    G : Graph
    osm : struct holding ways and nodes

    Examples
    --------
    >>> G=nx.read_osm(nx.download_osm(-122.33,47.60,-122.31,47.61))
    >>> plot([G.node[n]['data'].lat for n in G], [G.node[n]['data'].lon for n
        in G], ',')
    """
    osm = OSM(filename_or_stream)
    G = networkx.DiGraph()

    def addEdges(w):
        attr = w.tags
        attr['id'] = w.id
        if w.tags.get('highway') != 'footway':
            if w.tags.get('oneway') == '-1':
                G.add_path(reversed(w.nds), **attr)
            else:
                G.add_path(w.nds, **attr)
            """
            if 'oneway' not in w.tags and w.tags['highway'] != 'motorway':
                G.add_path(reversed(w.nds), **attr)
            elif (w.tags['oneway'] != 'yes' and w.tags['oneway'] != '-1' and
                  w.tags['highway'] != 'motorway'):
                G.add_path(reversed(w.nds), **attr)"""

    for w in osm.ways.itervalues():
        # Skip w if no highway tag
        if only_roads and 'highway' not in w.tags:
            continue
        addEdges(w)

    #RV
    #print '>> Num of nodes in G is %d' %(len(G.nodes()))
    #RV
    
    c = 0
    for n in osm.nodes:
	if (type(osm.nodes[n]) is BusStopNode):
		c += 1
	pass
    pass
    print "Number of busstop nodes is %d" %(c)
    
    for n_id in G.nodes_iter():
        n = osm.nodes[n_id]
        G.node[n_id] = dict(lon=n.lon, lat=n.lat)
    return G, osm


class Node(object):
    def __init__(self, id, lon, lat ):
        self.id = id
        self.lon = lon
        self.lat = lat
        self.tags = {}

class NonWayNode(Node):
    def __init__(self, id, lon, lat ,typeTag ):
        Node.__init__(self, id, lon, lat)
        self.typeTag = typeTag

class BusStopNode(NonWayNode):
    def __init__(self, id, lon, lat ):
        NonWayNode.__init__(self, id, lon, lat, 'bus_stop')


class Way:
    def __init__(self, id, osm):
        self.osm = osm
        self.id = id
        self.nds = []
        self.tags = {}

    def split(self, dividers):
        # slice the node-array using this nifty recursive function

        def slice_array(ar, dividers):
            for i in range(1, len(ar)-1):
                if dividers[ar[i]] > 1:
                    # print "slice at %s"%ar[i]
                    left = ar[:i + 1]
                    right = ar[i:]
                    rightsliced = slice_array(right, dividers)
                    return [left]+rightsliced
            return [ar]
        slices = slice_array(self.nds, dividers)
        # create a way object for each node-array slice
        ret = []
        i = 0
        for slice in slices:
            littleway = copy.copy(self)
            littleway.id += "-%d" % i
            littleway.nds = slice
            ret.append(littleway)
            i += 1
        return ret


class OSM:
    def __init__(self, filename_or_stream):
        """ File can be either a filename or stream/file object."""
        nodes = {}
        ways = {}
	busStops = {} # these are from NonWayNodes
        superself = self
	BsCount = 0

        class OSMHandler(object):
    	    def __init__(self, creator=None):
	    	self.creator = creator
		creator.BsCount = 0

            @classmethod
            def start(self, name, attrs):
    	    	try:
                	if attrs['action'].startswith("delete"):
                    		print "Deleting %s" %(attrs['id'])
				return  # ignore this element 
			pass
    	    	except:
                	if name == 'node':
                    		self.currElem = Node(attrs['id'], float(attrs['lon']), float(attrs['lat']))
                    		self.currElem.tags.update({'addBusstop': False})
                	elif name == 'way':
                    		self.currElem = Way(attrs['id'], superself)
				self.saveFirstNode = True
                    		self.currElem.tags.update({'addBusstop': False})
                	elif name == 'tag':
				if ((gIncBusStop == True) and ( (type(self.currElem) == Node) and attrs['v'] == 'bus_stop')):
					print 'Add bus stop node %s ' %(self.currElem.id)
                    			self.currElem.tags.update({'addBusstop': True})
				elif ((gIncBusStop == True) and ( isinstance(self.currElem, Way) and attrs['v'] == 'bus_stop')): # sometimes, busstops were found marked on a nd referred to by a way 
					print 'Found Way/busstop'
                    			lastitm = self.currElem.nds[-1]
                    			self.currElem.nds.remove(lastitm)
                    			self.currElem.tags.update({'addBusstop': True})
				pass
                    		self.currElem.tags[attrs['k']] = attrs['v']
				pass
                	elif name == 'nd':
                  		self.currElem.nds.append(attrs['ref'])
	    		pass

            @classmethod
            def end(self, name):
                if name == 'node':
                    newNode = tmpNode = self.currElem
		    if (tmpNode.tags.has_key('addBusstop')  and (tmpNode.tags['addBusstop']  == True)):
				if ( tmpNode.tags.has_key('asset_ref')):
					superself.BsCount += 1
					newNode = BusStopNode(tmpNode.id, float(tmpNode.lon), float(tmpNode.lat) )
					newNode.tags.update(tmpNode.tags)
					#print 'In end(): node %s %s at %f %f' % (newNode.id, newNode.tags['asset_ref'], newNode.lat, newNode.lon)
				else:
					print 'Bus stop without bus stop id -- skip'
				pass
		    pass
                    nodes[self.currElem.id] = newNode
                elif name == 'way':
                    ways[self.currElem.id] = self.currElem

            @classmethod
            def close(self):
                pass

        parser = etree.XMLParser(remove_blank_text=True, target=OSMHandler(self))
        etree.parse(filename_or_stream, parser)
        self.nodes = nodes
        #print '++Num of nodes is %d' %(len(self.nodes))
        self.ways = ways
        # count times each node is used
        node_histogram = dict.fromkeys(self.nodes.keys(), 0)
        for way in self.ways.values():
            if len(way.nds) < 2:
            # if a way has only one node, delete it out of the osm collection
                del self.ways[way.id]
            else:
                for node in way.nds:
                    node_histogram[node] += 1
        # use that histogram to split all ways, replacing the member set of
        # ways
        new_ways = {}
        for id, way in self.ways.iteritems():
            split_ways = way.split(node_histogram)
            for split_way in split_ways:
                new_ways[split_way.id] = split_way
        self.ways = new_ways

        #print '--Num of nodes is %d' %(len(self.nodes))
        #print '--Num of bus stops is %d' %(self.BsCount)

		
#read_osm("map.osm")
