#!/usr/bin/env python
""" VISSIM Tools """
from lxml import etree
from copy import deepcopy
from scipy.spatial.distance import cdist
import networkx as nx
from osm_to_graph import read_osm
from collections import OrderedDict
from pyproj import Proj


class Vissim(object):
    def __init__(self, filename=None):
        if filename is None:
            self.filename = 'default/default.inpx'
            self.data = self._load(self.filename)
        else:
            self.filename = filename
            self.data = self._load(filename)
        self.params = None
        self._getParams()
        self.links = Links(self.data, self.params)
        self.inputs = Inputs(self.data, self.params)
        self.routing = StaticRouting(self.data, self.params)

    def _load(self, filename):
        """ Load XML file """
        parser = etree.XMLParser(remove_blank_text=True)
        return etree.parse(filename, parser)

    def export(self, filename):
        """ Write XML file to disk """
        self.filename = filename
        self.data.write(filename, encoding="UTF-8", standalone=False,
                        pretty_print=True)

    def _getParams(self):
        """ Gets VISSIM network object parameters for integrity checks.
        """
        params = ['colorDistribution', 'conflictArea', 'desAcceleration',
                  'desDeceleration', 'desSpeedDistribution', 'displayType',
                  'drivingBehavior', 'linkBehaviorType', 'link',
                  'locatinDistribution', 'maxAcceleration', 'maxDeceleration',
                  'model2D3DDistribution', 'model2D3D',
                  'occupancyDistribution', 'pedestrianClass',
                  'pedestrianComposition', 'pedestrianType',
                  'powerDistribution', 'timeDistribution', 'vehicleClass',
                  'vehicleComposition', 'vehicleInput',
                  'vehicleRoutingDecisionStatic', 'vehicleType',
                  'walkingBehavior', 'weightDistribution']
        paramDict = {}
        for key in params:
            if key == 'maxDeceleration' or key == 'maxAcceleration':
                path = './' + key + 'Functions/' + key + '/@no'
            elif key == 'vehicleRoutingDecisionStatic':
                path = './vehicleRoutingDecisionsStatic/' + key + '/@no'
            elif key == 'vehicleClass':
                path = './vehicleClasses/' + key + '/@no'
            else:
                path = './' + key + 's/' + key + '/@no'
            paramDict[key] = {int(i) for i in self.data.xpath(path)}
        self.params = paramDict

    def _laneParse(self, lane):
        """ Takes lane attribute and splits it in to link and lane attributes.
        """
        link, laneStart = lane.split(' ')
        return {'connectLink': link, 'connectLane': laneStart}

    def _laneConcat(self, connectLink, connectLane):
        """ Takes link and lane attributes and combines them back in to a
            single attribute.
        """
        return str(connectLink) + ' ' + str(connectLane)

    def _getAttributes(self, attr, value, children=None, duplicate=True):
        """ Uses XPath to return attributes of Vissim object.
            Input: root attribute, root value, path to children (optional),
                   deep copy by default.
            Output: attribute dict of selected object
        """
        child = '' if children is None else children
        if attr not in self.types:
            raise KeyError('%s not a valid attribute' % (attr))
        xpath = (str(self.path) + '[@' + str(attr) + '="' + str(value) + '"]' +
                 str(child))
        data = self.data.xpath(xpath)
        if len(data) > 1:
            raise KeyError('Number of elements > 1')
        elif len(data) == 0:
            raise KeyError('Key does not exist')
        else:
            attribs = data[0].attrib
            if duplicate:
                attribs = deepcopy(attribs)
            if 'lane' in attribs:
                lane = self._laneParse(attribs['lane'])
                attribs.pop('lane')
                return dict(attribs, **lane)
            else:
                return attribs

    def _getChildren(self, attr, value, children, duplicate=True):
        """ Uses XPath to return children of a Vissim object
            Input: root attribute, root value, path to children, deep copy by
                   default.
            Output: List of children
        """
        if attr not in self.types:
            raise KeyError('%s not a valid attribute' % (attr))
        xpath = (self.path + '[@' + str(attr) + '="' + str(value) + '"]' +
                 str(children))
        if len(self.data.xpath(xpath)) == 0:
            raise KeyError('Key does not exist')
        else:
            childList = [i.attrib for i in self.data.xpath(xpath)]
            if duplicate:
                return deepcopy(childList)
            else:
                return childList

    def _setAttribute(self, attr, value, setAttr, setValue, children=None):
        child = '' if children is None else children
        path = (self.path + '[@' + str(attr) + '="' + str(value) + '"]' +
                str(child))
        data = self.data.xpath(path)
        if len(data) > 1:
            raise KeyError('Number of elements > 1')
        if setAttr == 'connectLink' and 'lane' in data[0].attrib.keys():
            attr = self._getAttributes(attr, value, children=children)
            connectLane = attr['connectLane']
            data[0].set('lane', self._laneConcat(setValue, connectLane))
        elif setAttr == 'connectLane' and 'lane' in data[0].attrib.keys():
            attr = self._getAttributes(attr, value, children=children)
            connectLane = attr['connectLink']
            data[0].set('lane', self._laneConcat(connectLink, setValue))
        elif setAttr in data[0].attrib.keys():
            data[0].set(setAttr, str(setValue))
            if setAttr == 'no':
                self._getParams()
        else:
            raise KeyError('%s not an attribute of element') % (setAttr)

    def _setChild(self, attr, value, element, elemAttr, children=None):
        child = '' if children is None else children
        path = (self.path + '[@' + str(attr) + '="' + str(value) + '"]' +
                str(child))
        data = self.data.xpath(path)
        if len(data) > 1:
            raise KeyError('Number of elements > 1')
        elif len(data) == 0:
            raise KeyError('%s path generates zero elements' % (path))
        if elemAttr is None:
            etree.SubElement(data[0], element)
        else:
            elemAttr = {str(k): str(v) for k, v in elemAttr.items()}
            etree.SubElement(data[0], element, attrib=elemAttr)
            if 'no' in elemAttr:
                self._getParams()

    def _removeChild(self, parent, child):
        data = self.data.xpath(parent)[0]
        data.remove(self.data.xpath(child)[0])
        self._getParams()

    def _getNewNum(self, key):
        nums = self.params[key]
        if len(nums) == 0:
            return 1
        else:
            return str(max(nums) + 1)

    def _getDefaultNum(self, key):
        nums = self.params[key]
        return str(list(nums)[0])

    def _parseLane(self, laneStr):
        """ Parse lane strings in to link and lane number """
        laneStr = str(laneStr)
        link, lane = laneStr.split(' ')
        return {'link': link, 'lane': lane}

    def createReference(self, x, y):
        """ Create coordinate system reference.
            Input: x, y points
            Output: reference network
        """
        if not self.data.xpath('./netPara'):
            a = {'concatMaxLen': "255", 'concatSeparator': ",",
                 'databFilename': "", 'drivSimActive': "false",
                 'leftHandTraffic': "false", 'northDir': "0",
                 'pedDefCellSize': "0.15", 'pedDefObstDist': "0.5",
                 'pedDirChgAngle': "4", 'pedDirChgClip': "true",
                 'pedNbhSearGridSize': "5", 'pedQueueOrder': "0.7",
                 'pedQueueStraight': "0.6", 'powWghtRatioMax': "30",
                 'powWghtRatioMin': "7", 'radExper': "2",
                 'sig3DColArrow': "false", 'unitAccel': "METRIC",
                 'unitLenLong': "IMPERIAL", 'unitLenShort': "IMPERIAL",
                 'unitLenVeryShort': "IMPERIAL", 'unitSpeed': "METRIC",
                 'unitSpeedSmall': "METRIC", 'useGradFromZCoord': "false"}
            etree.SubElement(self.data.getroot(), 'netPara', attrib=a)
        etree.SubElement(self.data.xpath('./netPara')[0], 'refPointMap',
                         attrib={'x': str(x), 'y': str(y)})
        etree.SubElement(self.data.xpath('./netPara')[0], 'refPointNet',
                         attrib={'x': '0', 'y': '0'})


class Links(Vissim):
    def __init__(self, data, params):
        self.path = './links/link'
        self.data = data
        self.params = params
        self.types = {'assumSpeedOncom': float, 'costPerKm': float,
                      'direction': str, 'displayType': int,
                      'emergStopDist': float, 'gradient': float,
                      'hasOvtLn': bool, 'isPedArea': bool, 'level': int,
                      'linkBehavType': int, 'linkEvalAct': bool,
                      'linkEvalSegLen': float, 'lnChgDist': float,
                      'lnChgEvalAct': bool, 'lookAheadDistOvt': float,
                      'mesoFollowUpGap': float, 'mesoSpeed': float,
                      'mesoSpeedModel': str, 'name': str, 'no': int,
                      'ovtOnlyPT': bool, 'ovtSpeedFact': float,
                      'showClsfValues': bool, 'showLinkBar': bool,
                      'showVeh': bool, 'surch1': float, 'surch2': float,
                      'thickness': float, 'vehRecAct': bool, 'geometry': list,
                      'lanes': list}

    def getLink(self, linkNum):
        """ Get attributes of link.
            Input: link number
            Output: Dict of link attributes
        """
        return self._getAttributes('no', linkNum)

    def getConnector(self, linkNum):
        """ Get attributes of connector.
            Input: link (connector) number
            Output: Dict of link and connector attributes
        """
        child1 = '/fromLinkEndPt'
        child2 = '/toLinkEndPt'
        linkAttr = self.getLink(linkNum)
        fromLink = self._getAttributes('no', linkNum, child1)
        toLink = self._getAttributes('no', linkNum, child2)
        return dict(linkAttr, **{'from': fromLink, 'to': toLink})

    def setLink(self, linkNum, attr, value):
        """ Set attribute of link.
            Input: link number
            Output: Changed link attribute
        """
        self._setAttribute('no', linkNum, attr, value)
        return self.getLink(linkNum)

    def setConnector(self, linkNum, attr, value, fromLink=True):
        if fromLink:
            child = '/fromLinkEndPt'
        elif not fromLink:
            child = '/toLinkEndPt'
        self._setAttribute('no', linkNum, attr, value, child)
        return self.getConnector(linkNum)

    def getGeometries(self, linkNum):
        """ Get link geometry.
            Input: link number
            Output: List of x,y,z tuples
        """
        children = '/geometry/points3D/point3D'
        return self._getChildren('no', linkNum, children)

    def addGeometry(self, linkNum, points):
        """ Add points to link's point set.
            Input: link number, list of x,y,z tuples
            Output: Added <point3D> elements to <points3D> elements
        """
        children = '/geometry/points3D'
        if isinstance(points, list):
            for x, y, z in points:
                a = {'x': x, 'y': y, 'zOffset': z}
                self._setChild('no', linkNum, 'point3D', a, children)
            return self.getGeometries(linkNum)
        else:
            raise TypeError('points must be list of tuples')

    def updateGeometry(self, linkNum, index, point):
        """ Update existing point set based on index.
            Input: link number, index to update, updated points tuple
            Output: return updated point set
        """
        children = '/geometry/points3D/point3D'
        geos = self._getChildren('no', linkNum, children, duplicate=False)
        if len(geos) > index:
            geos[index]['x'] = str(point[0])
            geos[index]['y'] = str(point[1])
            geos[index]['zOffset'] = str(point[2])
            return self.getGeometries(linkNum)
        else:
            raise IndexError('Index value does not exist in geos list')

    def getLanes(self, linkNum):
        """ Get lane widths.
            Input: link number
            Output: List of lane widths beginning with lane 1 (in meters)
        """
        return self._getChildren('no', linkNum, '/lanes/lane')

    def addLane(self, linkNum, lanes):
        """ Add lane widths to link's lane set.
            Input: link number, list of lane widths beginning with lane 1 (in
            meters)
            Output: Added <lane> elements to <lanes> element
        """
        if isinstance(lanes, list):
            for width in lanes:
                self._setChild('no', linkNum, 'lane',
                               {'width': width}, '/lanes')
            return self.getLanes(linkNum)
        else:
            raise TypeError('lanes must be a list of width values')

    def updateLane(self, linkNum, index, width):
        """ Update existing lane set based on index.
            Input: link number, index to update, update lane width value
            Output: return updated lane set
        """
        lanes = self._getChildren('no', linkNum, '/lanes/lane',
                                  duplicate=False)
        if len(lanes) > index:
            lanes[index]['width'] = str(width)
            return self.getLanes(linkNum)
        else:
            raise IndexError('Index value does not exist in lanes list')

    def getLinkLength(self, linkNum):
        """ Calculate length of a given link.
            Input: link number
            Output: link length in meters
        """
        geos = [(i['x'], i['y'], i['zOffset']) for i in
                self.getGeometries(linkNum)]
        return sum(cdist(geos[:-1], geos[1:]).diagonal())

    def createLink(self, **kwargs):
        """ Create a new link in the model.
            Input: link number, link, point3D and lane attributes as dict
            Output: Added <link> element to <links> element.
        """
        num = self._getNewNum('link')
        defaults = {'assumSpeedOncom': '60.00000', 'costPerKm': '0.00000',
                    'direction': 'ALL',
                    'displayType': self._getDefaultNum('displayType'),
                    'emergStopDist': '5.00000', 'gradient': '0.00000',
                    'hasOvtLn': 'false', 'isPedArea': 'false', 'level': '1',
                    'linkBehavType': self._getDefaultNum('linkBehaviorType'),
                    'linkEvalAct': 'false',
                    'linkEvalSegLen': '10.00000', 'lnChgDist': '200.00000',
                    'lnChgEvalAct': 'true', 'lookAheadDistOvt': '250.00000',
                    'mesoFollowUpGap': '0.00000', 'mesoSpeed': '50.00000',
                    'mesoSpeedModel': 'VEHICLEBASED', 'name': '',
                    'ovtOnlyPT': 'false', 'ovtSpeedFact': '1.300000',
                    'showClsfValues': 'true', 'showLinkBar': 'true',
                    'showVeh': 'true', 'surch1': '0.00000',
                    'surch2': '0.00000', 'thickness': '0.00000',
                    'vehRecAct': 'true', 'no': num}
        data = self.data
        a = {k: str(kwargs.get(k, v)) for k, v in defaults.items()}
        etree.SubElement(data.xpath('./links')[0], 'link', attrib=a)
        self._setChild('no', a['no'], 'geometry', None)
        self._setChild('no', a['no'], 'points3D', None, '/geometry')
        self.addGeometry(a['no'], kwargs.get('point3D',
                         [('0', '0', '0'), ('1', '1', '0')]))
        self._setChild('no', a['no'], 'lanes', None)
        self.addLane(a['no'], kwargs.get('lane', ['3.500000']))
        return self.getLink(a['no'])

    def createConnector(self, fromLink, fromLane, toLink, toLane, lanes, **kwargs):
        """ Create a new connector in the model.
            Input: from link, from lane, to link, to lane, attributes
            Output: Added <link> element to <links> element.
        """
        num = self._getNewNum('link')
        defaults = {'assumSpeedOncom': '60.00000', 'costPerKm': '0.00000',
                    'direction': 'ALL',
                    'displayType': self._getDefaultNum('displayType'),
                    'emergStopDist': '5.00000', 'gradient': '0.00000',
                    'hasOvtLn': 'false', 'isPedArea': 'false',
                    'linkBehavType': self._getDefaultNum('linkBehaviorType'),
                    'linkEvalAct': 'false',
                    'linkEvalSegLen': '10.00000', 'lnChgDist': '200.00000',
                    'lnChgDistIsPerLn': 'false',
                    'lnChgEvalAct': 'true', 'lookAheadDistOvt': '250.00000',
                    'mesoFollowUpGap': '0.00000', 'mesoSpeed': '50.00000',
                    'mesoSpeedModel': 'VEHICLEBASED', 'name': '',
                    'ovtOnlyPT': 'false', 'ovtSpeedFact': '1.300000',
                    'showClsfValues': 'true', 'showLinkBar': 'true',
                    'showVeh': 'true', 'surch1': '0.00000',
                    'surch2': '0.00000', 'thickness': '0.00000',
                    'vehRecAct': 'true', 'no': num}
        data = self.data
        a = {k: str(kwargs.get(k, v)) for k, v in defaults.items()}
        etree.SubElement(data.xpath('./links')[0], 'link', attrib=a)
        fromAttr = {'lane': str(fromLink) + ' ' + str(fromLane),
                    'pos': kwargs.get('fromPos', '0.0000')}
        self._setChild('no', a['no'], 'fromLinkEndPt', fromAttr)
        self._setChild('no', a['no'], 'geometry', None)
        self._setChild('no', a['no'], 'points3D', None, '/geometry')
        self.addGeometry(a['no'], kwargs.get('point3D',
                         [('0', '0', '0'), ('1', '1', '0')]))
        self._setChild('no', a['no'], 'lanes', None)
        # Check number of lanes doesn't exceed the number of from/to lanes
        if len(self.getLanes(fromLink)) >= lanes and len(self.getLanes(toLink)) >= lanes:
            for lane in range(lanes):
                self._setChild('no', a['no'], 'lane', None, '/lanes')
        else:
            raise ValueError('Number of lanes exceeds number of from/to lanes')
        toAttr = {'lane': str(toLink) + ' ' + str(toLane),
                  'pos': kwargs.get('toPos', self.getLinkLength(toLink))}
        self._setChild('no', a['no'], 'toLinkEndPt', toAttr)
        return self.getConnector(a['no'])

    def removeLink(self, linkNum):
        """ Remove an existing link or connector from the model.
            Input: link number
            Output: Removed <link> element from <links> element
        """
        parent = './links'
        child = self.path + '[@no="' + str(linkNum) + '"]'
        self._removeChild(parent, child)


class Inputs(Vissim):
    def __init__(self, data, params):
        self.path = './vehicleInputs/vehicleInput'
        self.data = data
        self.params = params
        self.types = {'anmFlag': bool, 'link': int, 'name': str, 'no': int}

    def getInput(self, attr, value):
        """ Get attributes for a given input based on input attribute value.
            Input: Input attribute = value
            Output: dict of attributes
        """
        return self._getAttributes(attr, value)

    def setInput(self, inputNum, attr, value):
        """ Set attribute of input.
            Input: input number
            Output: Changed input attribute
        """
        self._setAttribute('no', inputNum, attr, value)
        return self.getInput('no', inputNum)

    def getVols(self, inputNum):
        """ Get attributes of volume.
            Input: input number
            Output: List of volume profiles
        """
        children = '/timeIntVehVols/timeIntervalVehVolume'
        return self._getChildren('no', inputNum, children)

    def addVol(self, inputNum, vol, **kwargs):
        """ Add a new volume profile to input.
            Input: input number
            Output: Updated list of volume profiles
        """
        defaults = {'cont': 'false', 'timeInt': '1 0',
                    'vehComp': self._getDefaultNum('vehicleComposition'),
                    'volType': 'EXACT'}
        a = {k: kwargs.get(k, v) for k, v in defaults.items()}
        a['volume'] = vol
        self._setChild('no', inputNum, 'timeIntervalVehVolume', a,
                       '/timeIntVehVols')
        return self.getVols(inputNum)

    def updateVol(self, inputNum, index, vol):
        """ Update existing volume value based on index.
            Input: input number, index, new volume value
            Output: Updated list of volume profiles
        """
        children = '/timeIntVehVols/timeIntervalVehVolume'
        vols = self._getChildren('no', inputNum, children, duplicate=False)
        if len(vols) > index:
            vols[index]['volume'] = str(vol)
            return self.getVols(inputNum)
        else:
            raise IndexError('Index value does not exist in volume list')

    def createInput(self, linkNum, vol, **kwargs):
        """ Create a new input in the model.
            Input: input number, input and volume attributes as dict
            Output: Added <vehicleInput> element to <vehicleInputs> element.
        """
        defaults = {'anmFlag': 'false', 'name': '',
                    'no': self._getNewNum('vehicleInput')}
        data = self.data
        a = {k: str(kwargs.get(k, v)) for k, v in defaults.items()}
        a['link'] = str(linkNum)
        etree.SubElement(data.xpath('./vehicleInputs')[0], 'vehicleInput',
                         attrib=a)
        self._setChild('no', a['no'], 'timeIntVehVols', None)
        self.addVol(a['no'], vol, **kwargs)
        return self.getInput('no', a['no'])

    def removeInput(self, inputNum):
        """ Remove an existing input from the model.
            Input: input number
            Output: Removed <vehicleInput> element from <vehicleInputs> element
        """
        parent = './vehicleInputs'
        child = self.path + '[@no="' + str(inputNum) + '"]'
        self._removeChild(parent, child)


class StaticRouting(Vissim):
    def __init__(self, data, params):
        self.path = './vehicleRoutingDecisionsStatic/' \
                    'vehicleRoutingDecisionStatic'
        self.data = data
        self.params = params
        self.types = {'allVehTypes': bool, 'anmFlag': bool,
                      'combineStaRoutDec': bool, 'link': int, 'name': str,
                      'no': int, 'pos': float, 'destLink': int,
                      'destPos': float, 'relFlow': float}

    def removeRoute(self, routingNum, routeNum):
        """ Remove an existing route from the model.
            Input: routing decision number, route number
            Output: Removed <vehicleRouteStatic> element from
            <vehRoutSta> element
        """
        parent = self.path + '[@no="' + str(routingNum) + '"]/vehRoutSta'
        child = parent + '/vehicleRouteStatic[@no="' + str(routeNum) + '"]'
        self._removeChild(parent, child)

    def removeRouting(self, routingNum):
        parent = './vehicleRoutingDecisionsStatic'
        child = (self.path + '[@no="' + str(routingNum) + '"]')
        self._removeChild(parent, child)

    def getRouting(self, attr, value):
        """ Get attributes for a given routing decision based on attribute
            value.
            Input: Routing decision attribute = value
            Output: dict of attributes
        """
        return self._getAttributes(attr, value)

    def setRouting(self, routingNum, attr, value):
        """ Set attribute of routing decision.
            Input: routing decision number, attribute, set value
            Output: Changed routing decision attribute
        """
        self._setAttribute('no', routingNum, attr, value)
        return self.getRouting('no', routingNum)

    def getVehicleClasses(self, routingNum):
        """ Get vehicle classes associated with routing decision.
            Input: routing decision number
            Output: list of vehicle classes
        """
        children = '/vehClasses/intObjectRef'
        return self._getChildren('no', routingNum, children)

    def setVehicleClasses(self, routingNum, classes):
        """ Set vehicle classes.
            Input: routing decision number, list of vehicle classes
            Output: Added <intObjectRef> elements to <vehClasses> element
        """
        if isinstance(classes, list):
            for c in classes:
                self._setChild('no', routingNum, 'intObjectRef',
                               {'key': c}, '/vehClasses')
            return self.getVehicleClasses(routingNum)
        else:
            raise TypeError('classes must be a list of vehicle classes')

    def getRoutes(self, routingNum):
        """ Get list of routes for a given routing decision.
            Input: routing decision number
            Output: list of routes
        """
        children = '/vehRoutSta/vehicleRouteStatic'
        return self._getChildren('no', routingNum, children)

    def getRoute(self, routingNum, attr, value):
        """ Get attributes for a given route based on attribute value.
            Input: Routing decision number, Route attribute = value
            Output: dict of attributes
        """
        child = ('/vehRoutSta/vehicleRouteStatic[@' + str(attr) + '="' +
                 str(value) + '"]')
        return self._getAttributes('no', routingNum, child)

    def setRoute(self, routingNum, routeNum, attr, value):
        """ Set attribute of route.
            Input: routing decision number, route number, attribute, set value
            Output: Changed route attribute
        """
        child = '/vehRoutSta/vehicleRouteStatic[@no="' + str(routeNum) + '"]'
        self._setAttribute('no', routingNum, attr, value, child)
        return self.getRoute(routingNum, 'no', routeNum)

    def updateFlow(self, routingNum, routeNum, volume):
        """ Update the relative flow value of a given route in a routing
            decision.
            Input: routing decision number, route number, flow
            Output: updated route dict
        """
        child = ('/vehRoutSta/vehicleRouteStatic[@no="' +
                 str(routeNum) + '"]')
        flow = self._getAttributes('no', routingNum, child, duplicate=False)
        prefix = flow['relFlow'].split(':')[0]
        value = prefix + ':' + str(volume)
        self.setRoute(routingNum, routeNum, 'relFlow', value)
        return self.getRoute(routingNum, 'no', routeNum)

    def getRouteSeqs(self, routingNum, routeNum):
        """ Get sequence of links that a given route traverses.
            Input: routing decision number, route number
            Output: list of links in order
        """
        children = ('/vehRoutSta/vehicleRouteStatic[@no="' + str(routeNum) +
                    '"]/linkSeq/intObjectRef')
        return self._getChildren('no', routingNum, children)

    def addRouteSeq(self, routingNum, routeNum, links):
        """ Set sequence of links that a given route traverses.
            Input: routing decision number, route number, list of links
            Output: Added <intObjectRef> elements to <linkSeq> element
        """
        children = ('/vehRoutSta/vehicleRouteStatic[@no="' + str(routeNum) +
                    '"]/linkSeq')
        if isinstance(links, list):
            if len(links) == 0:
                return []
            else:
                for link in links:
                    a = {'key': int(link)}
                    self._setChild('no', routingNum, 'intObjectRef', a,
                                   children)
                return self.getRouteSeqs(routingNum, routeNum)
        else:
            raise TypeError('links must be list of integers')

    def updateRouteSeq(self, routingNum, routeNum, index, link):
        """ Update existing route sequence based on index
            Input: routing decision number, route number, index of links
            Output: list of links in order
        """
        children = ('/vehRoutSta/vehicleRouteStatic[@no="' + str(routeNum) +
                    '"]/linkSeq/intObjectRef')
        seqs = self._getChildren('no', routingNum, children, duplicate=False)
        if len(seqs) > index:
            seqs[index]['key'] = str(link)
            return self.getRouteSeqs(routingNum, routeNum)
        else:
            raise IndexError('Index value does not exist in sequence list')

    def createRoute(self, routingNum, destLink, **kwargs):
        num = (self.data.xpath(self.path + '[@no="' + str(routingNum) +
               '"]/vehRoutSta/vehicleRouteStatic/@no'))
        if len(num) == 0:
            num = '1'
        else:
            num = str(max(num) + 1)
        defaults = {'destPos': '0.000', 'name': '', 'no': num, 'relFlow': ''}
        data = self.data
        a = {k: kwargs.get(k, v) for k, v in defaults.items()}
        a['destLink'] = str(destLink)
        self._setChild('no', routingNum, 'vehicleRouteStatic', a,
                       '/vehRoutSta')
        child = '/vehRoutSta/vehicleRouteStatic[@no="' + str(num) + '"]'
        self._setChild('no', routingNum, 'linkSeq', None, child)
        self.addRouteSeq(routingNum, num, kwargs.get('linkSeq', []))
        return self.getRoute(routingNum, 'no', a['no'])

    def createRouting(self, linkNum, **kwargs):
        """ Create a new routing decision in the model.
            Input: link number and attributes as dict
            Output: Added <vehicleRoutingDecisionStatic> element to
            <vehicleRoutingDecisionsStatic> element.
        """
        num = self._getNewNum('vehicleRoutingDecisionStatic')
        defaults = {'allVehTypes': 'false', 'anmFlag': 'false', 'no': num,
                    'combineStaRoutDec': 'false', 'name': '', 'pos': '0.0000'}
        data = self.data
        a = {k: kwargs.get(k, v) for k, v in defaults.items()}
        a['link'] = str(linkNum)
        etree.SubElement(data.xpath('./vehicleRoutingDecisionsStatic')[0],
                         'vehicleRoutingDecisionStatic', attrib=a)
        self._setChild('no', a['no'], 'vehClasses', None)
        self.setVehicleClasses(a['no'], kwargs.get('vehClasses',
                               self._getDefaultNum('vehicleClass')))
        self._setChild('no', a['no'], 'vehRoutSta', None)
        return self.getRouting('no', a['no'])


class OSM(Vissim):
    def __init__(self, osmFile):
        self.G = read_osm(osmFile)
        self.latlng = self.createLinkDict()
        self.proj = Proj(init='epsg:3857')
        self.refLng = self.latlng[1]['links'][0][1]  # First x
        self.refLat = self.latlng[1]['links'][0][0]  # First y
        self.xy = {k: self.convertLatLng(v['links'], self.refLng, self.refLat)
                   for k, v in self.latlng.items()}
        self.v = Vissim()
        self.refX, self.refY = self.latLngToMeters(self.refLat, self.refLng)
        self.v.createReference(self.refX, self.refY)

    def isModelEdge(self, n):
        """ If a node has only one neighbor node, it's at the edge of the model.
        """
        if len(set(self.G.successors(n) + self.G.predecessors(n))) == 1:
            # These are one-way start points, or bi-directional end points
            return True
        else:
            return False

    def isIntersection(self, n):
        """ If node has more than two connecting nodes, it's an intersection.
        """
        if len(set(self.G.successors(n) + self.G.predecessors(n))) > 2:
            return True
        else:
            return False

    def isDiscontinuous(self, n, nodeList):
        if nodeList == []:
            return False
        else:
            if nodeList[-1][1] != n:
                return True
            else:
                return False

    def latLngToMeters(self, lat, lng):
        """ Convert lat/lng to meters from 0,0 point on WGS84 map.
            Input: WGS84 lat/lng
            Output: x,y in meters
        """
        # Weird fudge factor due to PTVs coordinate system
        yCorrection = 7500
        x, y = self.proj(lng, lat)
        y = y + yCorrection
        return x, y

    def convertLatLng(self, latLng, refLat, refLng):
        """ Convert WGS84 lat/lng to VISSIM's reference coordinate system
            Input: list of WGS84 lat/lng, zero-point lat/lng
            Output: list of x, y in meters relative to reference point
        """
        refX, refY = self.latLngToMeters(refLat, refLng)
        xy = [self.latLngToMeters(lat, lng) for lng, lat in latLng]
        return [(str(x - refX), str(y - refY), '0') for x, y in xy]

    def getLatLng(self, n):
        """ Return lat/lng tuple for a given node.
        """
        return (self.G.node[n]['lon'], self.G.node[n]['lat'])

    def getEdgeNodes(self):
        """ Get a list of nodes at the edge of the graph.
        """
        nodes = []
        for n in self.G.nodes():
            if self.isModelEdge(n):
                nodes.append(n)
        return nodes

    def getStartNodes(self):
        """ Get a list of nodes that do not overlap when traversed.
        """
        edgeNodes = self.getEdgeNodes()
        for node in edgeNodes:
            for prev, n in nx.dfs_edges(self.G, source=node):
                if n in edgeNodes:
                    edgeNodes.remove(n)
        return edgeNodes

    def getLinks(self, startNode, startValue=1):
        """ Begin with startNode and end at an intersection
            Input: graph, startNode
            Output: nodes that comprise a single link
        """
        links = {}
        link = startValue
        tuples = []
        edgeNodes = self.getEdgeNodes()
        for prev, n in nx.dfs_edges(self.G, source=startNode):
            if self.isDiscontinuous(prev, tuples):
                # If we encounter a new way, close out current link and start a
                # new one
                latlng = [self.getLatLng(e) for l in tuples for e in l]
                links[link] = {}
                links[link]['links'] = list(OrderedDict.fromkeys(latlng))
                links[link]['attr'] = self.G.edge[prev][n]
                link += 1
                tuples = [(prev, n)]
            elif self.isIntersection(n) or n in edgeNodes:
                # If we encounter an intersection or the edge of model,
                # close out current link and start a new one
                tuples.append((prev, n))
                latlng = [self.getLatLng(e) for l in tuples for e in l]
                links[link] = {}
                links[link]['links'] = list(OrderedDict.fromkeys(latlng))
                links[link]['attr'] = self.G.edge[prev][n]
                link += 1
                tuples = []
            else:
                tuples.append((prev, n))
        return links

    def createLinkDict(self):
        """ Create a dictionary with link number as key, list of anchor
            points as values.
        """
        links = {}
        startValue = 1
        startNodes = self.getStartNodes()
        for n in startNodes:
            links.update(self.getLinks(n, startValue))
            startValue = max(links.keys()) + 1
        return links

    def importLinks(self):
        """ Create links based on loaded OSM data.
            Input: object xy values
            Output: returns vissim object with added links
        """
        for key, value in self.xy.items():
            self.v.links.createLink(**{'no': key, 'point3D': value})

    def drawLinks(self, links):
        """ Plot links for viewing
        """
        from matplotlib.pyplot import plot
        for i in links.keys():
            plot([j[0] for j in links[i]], [j[1] for j in links[i]])