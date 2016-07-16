#!/usr/bin/env python
""" VISSIM Tools """
from lxml import etree


class Vissim(object):
    def __init__(self, filename=None):
        if filename is None:
            self.filename = 'default.inpx'
            self.data = self._new()
        else:
            self.filename = filename
            self.data = self._load(filename)

        def _getParams(key):
            if key == 'maxDeceleration' or key == 'maxAcceleration':
                path = './' + key + 'Functions/' + key + '/@no'
            elif key == 'vehicleRoutingDecisionStatic':
                path = './vehicleRoutingDecisionsStatic/' + key + '/@no'
            elif key == 'vehicleClass':
                path = './vehicleClasses/' + key + '/@no'
            else:
                path = './' + key + 's/' + key + '/@no'
            return {int(i) for i in self.data.xpath(path)}
        self.paramKeys = ['colorDistribution', 'conflictArea',
                          'desAcceleration', 'desDeceleration',
                          'desSpeedDistribution', 'displayType',
                          'drivingBehavior', 'linkBehaviorType', 'link',
                          'locatinDistribution', 'maxAcceleration',
                          'maxDeceleration', 'model2D3DDistribution',
                          'model2D3D', 'occupancyDistribution',
                          'pedestrianClass',
                          'pedestrianComposition', 'pedestrianType',
                          'powerDistribution', 'timeDistribution',
                          'vehicleClass', 'vehicleComposition',
                          'vehicleInput', 'vehicleRoutingDecisionStatic',
                          'vehicleType', 'walkingBehavior',
                          'weightDistribution']
        self.params = {k: _getParams(k) for k in self.paramKeys}
        self.links = Links(self.data, self.params)
        self.inputs = Inputs(self.data, self.params)
        self.routing = StaticRouting(self.data, self.params)

    def _load(self, filename):
        """ Load XML file """
        f = open(filename, 'r')
        parser = etree.XMLParser(remove_blank_text=True)
        return etree.parse(f, parser=parser)

    def _new(self):
        """ Load default blank VISSIM model """
        return self._load('default.inpx')

    def export(self, filename):
        """ Write XML file to disk """
        self.data.write(filename, encoding="UTF-8", standalone=False,
                        pretty_print=True)

    def _getAttributes(self, attr, value, children=None):
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
            return data[0].attrib

    def _getChildren(self, attr, value, children):
        if attr not in self.types:
            raise KeyError('%s not a valid attribute' % (attr))
        xpath = (self.path + '[@' + str(attr) + '="' + str(value) + '"]' +
                 str(children))
        if len(self.data.xpath(xpath)) == 0:
            raise KeyError('Key does not exist')
        else:
            return [i.attrib for i in self.data.xpath(xpath)]

    def _setAttribute(self, attr, value, setAttr, setValue, children=None):
        child = '' if children is None else children
        path = (self.path + '[@' + str(attr) + '="' + str(value) + '"]' +
                str(child))
        data = self.data.xpath(path)
        if len(data) > 1:
            raise KeyError('Number of elements > 1')
        if setAttr in data[0].attrib.keys():
            data[0].set(setAttr, str(setValue))
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

    def _removeChild(self, parent, child):
        data = self.data.xpath(parent)[0]
        data.remove(self.data.xpath(child)[0])

    def _getNewNum(self, key):
        nums = self.params[key]
        if len(nums) == 0:
            return 1
        else:
            return max(nums) + 1

    def _getDefaultNum(self, key):
        nums = self.params[key]
        return list(nums)[0]


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

    def setLink(self, linkNum, attr, value):
        """ Set attribute of link.
            Input: link number
            Output: Changed link attribute
        """
        self._setAttribute('no', linkNum, attr, value)
        return self.getLink(linkNum)

    def getGeometry(self, linkNum):
        """ Get link geometry.
            Input: link number
            Output: List of x,y,z tuples
        """
        children = '/geometry/points3D/point3D'
        return self._getChildren('no', linkNum, children)

    def setGeometry(self, linkNum, points):
        """ Set link geometry.
            Input: link number, list of x,y,z tuples
            Output: Added <point3D> elements to <points3D> elements
        """
        children = '/geometry/points3D'
        if isinstance(points, list):
            for x, y, z in points:
                a = {'x': x, 'y': y, 'zOffset': z}
                self._setChild('no', linkNum, 'point3D', a, children)
            return self.getGeometry(linkNum)
        else:
            raise TypeError('points must be list of tuples')

    def getLanes(self, linkNum):
        """ Get lane widths.
            Input: link number
            Output: List of lane widths beginning with lane 1 (in meters)
        """
        return self._getChildren('no', linkNum, '/lanes/lane')

    def setLanes(self, linkNum, lanes):
        """ Set lane widths.
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
        a = {k: kwargs.get(k, v) for k, v in defaults.items()}
        etree.SubElement(data.xpath('./links')[0], 'link', attrib=a)
        self._setChild('no', a['no'], 'geometry', None)
        self._setChild('no', a['no'], 'points3D', None, '/geometry')
        self.setGeometry(a['no'], kwargs.get('point3D',
                         [('0', '0', '0'), ('1', '1', '0')]))
        self._setChild('no', a['no'], 'lanes', None)
        self.setLanes(a['no'], kwargs.get('lane', ['3.500000']))
        return self.getLink(a['no'])

    def removeLink(self, linkNum):
        """ Remove an existing link from the model.
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
            Output: Dict of volume attributes
        """
        children = '/timeIntVehVols/timeIntervalVehVolume'
        return self._getChildren('no', inputNum, children)

    def setVols(self, inputNum, vol, **kwargs):
        """ Set attribute of volume.
            Input: input number
            Output: Changed volume attribute
        """
        defaults = {'cont': 'false', 'timeInt': '1 0',
                    'vehComp': self._getDefaultNum('vehicleComposition'),
                    'volType': 'EXACT'}
        a = {k: kwargs.get(k, v) for k, v in defaults.items()}
        a['volume'] = vol
        self._setChild('no', inputNum, 'timeIntervalVehVolume', a,
                       '/timeIntVehVols')
        return self.getVols(inputNum)

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
        self.setVols(a['no'], vol, **kwargs)
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

    def getRouteSeq(self, routingNum, routeNum):
        """ Get sequence of links that a given route traverses.
            Input: routing decision number, route number
            Output: list of links in order
        """
        children = ('/vehRoutSta/vehicleRouteStatic[@no="' + str(routeNum) +
                    '"]/linkSeq/intObjectRef')
        return self._getChildren('no', routingNum, children)

    def setRouteSeq(self, routingNum, routeNum, links):
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
                return self.getRouteSeq(routingNum, routeNum)
        else:
            raise TypeError('links must be list of integers')

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
        self.setRouteSeq(routingNum, num, kwargs.get('linkSeq', []))
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
