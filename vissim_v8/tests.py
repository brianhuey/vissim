import unittest
import vissim_v8 as vissim

network = 'test_networks/Busmall.inpx'


class link_unittest(unittest.TestCase):
    def setUp(self):
        self.v = vissim.Vissim(network)
        self.links = self.v.links
        self.maxDiff = None

    def test_getLink(self):
        answer = {'showVeh': 'true', 'assumSpeedOncom': '60.000000',
                  'hasOvtLn': 'false', 'costPerKm': '0.000000',
                  'lnChgDist': '200.000000', 'showClsfValues': 'true',
                  'mesoSpeedModel': 'VEHICLEBASED', 'no': '1',
                  'gradient': '0.000000', 'showLinkBar': 'true',
                  'thickness': '0.000000', 'displayType': '1',
                  'surch2': '0.000000', 'surch1': '0.000000',
                  'mesoFollowUpGap': '0.000000', 'linkEvalAct': 'false',
                  'linkEvalSegLen': '10.000000', 'direction': 'ALL',
                  'lnChgDistIsPerLn': 'false', 'ovtSpeedFact': '1.300000',
                  'ovtOnlyPT': 'false', 'lookAheadDistOvt': '250.000000',
                  'mesoSpeed': '50.000000', 'name': '', 'level': '1',
                  'isPedArea': 'false', 'emergStopDist': '5.000000',
                  'linkBehavType': '1', 'lnChgEvalAct': 'true',
                  'vehRecAct': 'true'}
        self.assertEqual(self.links.getLink(1), answer)

    def test_getConnector(self):
        answer = {'assumSpeedOncom': '60.000000', 'costPerKm': '0.000000',
                  'direction': 'ALL', 'displayType': '1',
                  'emergStopDist': '5.000000', 'from': {'connectLink': '4',
                                                        'connectLane': '1',
                                                        'pos': '198.991000'},
                  'gradient': '0.000000', 'hasOvtLn': 'false',
                  'isPedArea': 'false', 'linkBehavType': '1',
                  'linkEvalAct': 'false', 'linkEvalSegLen': '10.000000',
                  'lnChgDist': '200.000000', 'lnChgDistIsPerLn': 'false',
                  'lnChgEvalAct': 'true', 'lookAheadDistOvt': '250.000000',
                  'mesoFollowUpGap': '0.000000', 'mesoSpeed': '50.000000',
                  'mesoSpeedModel': 'VEHICLEBASED', 'name': '', 'no': '10080',
                  'ovtOnlyPT': 'false', 'ovtSpeedFact': '1.300000',
                  'showClsfValues': 'true', 'showLinkBar': 'true',
                  'showVeh': 'true', 'surch1': '0.000000',
                  'surch2': '0.000000',
                  'thickness': '0.000000', 'to': {'connectLink': '63',
                                                  'connectLane': '1',
                                                  'pos': '0.271000'},
                  'vehRecAct': 'true'}
        self.assertEqual(self.links.getConnector(10080), answer)

    def test_setLink(self):
        answer = {'showVeh': 'true', 'assumSpeedOncom': '60.000000',
                  'hasOvtLn': 'false', 'costPerKm': '0.000000',
                  'lnChgDist': '200.000000', 'showClsfValues': 'true',
                  'mesoSpeedModel': 'VEHICLEBASED', 'no': '1',
                  'gradient': '0.000000', 'showLinkBar': 'true',
                  'thickness': '0.000000', 'displayType': '2',
                  'surch2': '0.000000', 'surch1': '0.000000',
                  'mesoFollowUpGap': '0.000000', 'linkEvalAct': 'false',
                  'linkEvalSegLen': '10.000000', 'direction': 'ALL',
                  'lnChgDistIsPerLn': 'false', 'ovtSpeedFact': '1.300000',
                  'ovtOnlyPT': 'false', 'lookAheadDistOvt': '250.000000',
                  'mesoSpeed': '50.000000', 'name': '', 'level': '1',
                  'isPedArea': 'false', 'emergStopDist': '5.000000',
                  'linkBehavType': '1', 'lnChgEvalAct': 'true',
                  'vehRecAct': 'true'}
        self.assertEqual(self.links.setLink(1, 'displayType', '2'), answer)

    def test_setConnector(self):
        answer = {'assumSpeedOncom': '60.000000', 'costPerKm': '0.000000',
                  'direction': 'ALL', 'displayType': '1',
                  'emergStopDist': '5.000000', 'from': {'connectLink': '4',
                                                        'connectLane': '1',
                                                        'pos': '198.991000'},
                  'gradient': '0.000000', 'hasOvtLn': 'false',
                  'isPedArea': 'false', 'linkBehavType': '1',
                  'linkEvalAct': 'false', 'linkEvalSegLen': '10.000000',
                  'lnChgDist': '200.000000', 'lnChgDistIsPerLn': 'false',
                  'lnChgEvalAct': 'true', 'lookAheadDistOvt': '250.000000',
                  'mesoFollowUpGap': '0.000000', 'mesoSpeed': '50.000000',
                  'mesoSpeedModel': 'VEHICLEBASED', 'name': '', 'no': '10080',
                  'ovtOnlyPT': 'false', 'ovtSpeedFact': '1.300000',
                  'showClsfValues': 'true', 'showLinkBar': 'true',
                  'showVeh': 'true', 'surch1': '0.000000',
                  'surch2': '0.000000',
                  'thickness': '0.000000', 'to': {'connectLink': '63',
                                                  'connectLane': '1',
                                                  'pos': '0.0000'},
                  'vehRecAct': 'true'}
        self.assertEqual(self.links.setConnector(10080, 'pos', '0.0000',
                                                 fromLink=False), answer)

    def test_getGeometries(self):
        answer = [{'y': '3786.952000', 'x': '-282.116000',
                   'zOffset': '0.000000'},
                  {'y': '4007.169000', 'x': '-285.973000',
                   'zOffset': '0.000000'}]
        self.assertEqual(self.links.getGeometries(1), answer)

    def test_addGeometry(self):
        answer = [{'y': '3786.952000', 'x': '-282.116000',
                   'zOffset': '0.000000'},
                  {'y': '4007.169000', 'x': '-285.973000',
                   'zOffset': '0.000000'},
                  {'y': '2', 'x': '1', 'zOffset': '3'}]
        self.assertEqual(self.links.addGeometry(1, [(1, 2, 3)]), answer)

    def test_updateGeometry(self):
        answer = [{'y': '3786.952000', 'x': '-282.116000',
                   'zOffset': '0.000000'},
                  {'y': '2.1', 'x': '1.1',
                   'zOffset': '3.1'}]
        self.assertEqual(self.links.updateGeometry(1, 1, (1.1, 2.1, 3.1)),
                         answer)

    def test_getLanes(self):
        answer = [{'width': '3.500000'}, {'width': '3.500000'},
                  {'width': '3.500000'}]
        self.assertEqual(self.links.getLanes(3), answer)

    def test_addLane(self):
        answer = [{'width': '3.500000'}, {'width': '3.500000'},
                  {'width': '3.500000'}, {'width': '3.5'}, {'width': '3.5'}]
        self.assertEqual(self.links.addLane(3, [3.5, 3.5]), answer)

    def test_updateLane(self):
        answer = [{'width': '3.500000'}, {'width': '5.0'},
                  {'width': '3.500000'}]
        self.assertEqual(self.links.updateLane(3, 1, 5.0), answer)

    def test_createLink(self):
        defaults = {'assumSpeedOncom': '60.00000', 'costPerKm': '0.00000',
                    'direction': 'ALL',
                    'displayType': '1',
                    'emergStopDist': '5.00000', 'gradient': '0.00000',
                    'hasOvtLn': 'false', 'isPedArea': 'false', 'level': '1',
                    'linkBehavType': '1',
                    'linkEvalAct': 'false',
                    'linkEvalSegLen': '10.00000', 'lnChgDist': '200.00000',
                    'lnChgEvalAct': 'true', 'lookAheadDistOvt': '250.00000',
                    'mesoFollowUpGap': '0.00000', 'mesoSpeed': '50.00000',
                    'mesoSpeedModel': 'VEHICLEBASED', 'name': '',
                    'ovtOnlyPT': 'false', 'ovtSpeedFact': '1.300000',
                    'showClsfValues': 'true', 'showLinkBar': 'true',
                    'showVeh': 'true', 'surch1': '0.00000',
                    'surch2': '0.00000', 'thickness': '0.00000',
                    'vehRecAct': 'true', 'no': '6000'}
        self.assertEqual(self.links.createLink(**defaults), defaults)

    def test_createConnector(self):
        defaults = {'assumSpeedOncom': '60.000000', 'costPerKm': '0.000000',
                    'direction': 'ALL', 'displayType': '1',
                    'emergStopDist': '5.000000', 'fromPos': '0.0000',
                    'gradient': '0.000000', 'hasOvtLn': 'false',
                    'isPedArea': 'false', 'linkBehavType': '1',
                    'linkEvalAct': 'false', 'linkEvalSegLen': '10.000000',
                    'lnChgDist': '200.000000', 'lnChgDistIsPerLn': 'false',
                    'lnChgEvalAct': 'true', 'lookAheadDistOvt': '250.000000',
                    'mesoFollowUpGap': '0.000000', 'mesoSpeed': '50.000000',
                    'mesoSpeedModel': 'VEHICLEBASED', 'name': '',
                    'no': '90000',
                    'ovtOnlyPT': 'false', 'ovtSpeedFact': '1.300000',
                    'showClsfValues': 'true', 'showLinkBar': 'true',
                    'showVeh': 'true', 'surch1': '0.000000',
                    'surch2': '0.000000',
                    'thickness': '0.000000', 'toPos': '5.000',
                    'vehRecAct': 'true'}
        answer = {'assumSpeedOncom': '60.000000', 'costPerKm': '0.000000',
                  'direction': 'ALL', 'displayType': '1',
                  'emergStopDist': '5.000000', 'from': {'connectLink': '2',
                                                        'connectLane': '1',
                                                        'pos': '0.0000'},
                  'gradient': '0.000000', 'hasOvtLn': 'false',
                  'isPedArea': 'false', 'linkBehavType': '1',
                  'linkEvalAct': 'false', 'linkEvalSegLen': '10.000000',
                  'lnChgDist': '200.000000', 'lnChgDistIsPerLn': 'false',
                  'lnChgEvalAct': 'true', 'lookAheadDistOvt': '250.000000',
                  'mesoFollowUpGap': '0.000000', 'mesoSpeed': '50.000000',
                  'mesoSpeedModel': 'VEHICLEBASED', 'name': '', 'no': '90000',
                  'ovtOnlyPT': 'false', 'ovtSpeedFact': '1.300000',
                  'showClsfValues': 'true', 'showLinkBar': 'true',
                  'showVeh': 'true', 'surch1': '0.000000',
                  'surch2': '0.000000',
                  'thickness': '0.000000', 'to': {'connectLink': '3',
                                                  'connectLane': '1',
                                                  'pos': '5.000'},
                  'vehRecAct': 'true'}
        self.assertEqual(self.links.createConnector(2, 1, 3, 1, 1, **defaults),
                         answer)

    def test_removeLink(self):
        answer = {'showVeh': 'true', 'assumSpeedOncom': '60.000000',
                  'hasOvtLn': 'false', 'costPerKm': '0.000000',
                  'lnChgDist': '200.000000', 'showClsfValues': 'true',
                  'mesoSpeedModel': 'VEHICLEBASED', 'no': '1',
                  'gradient': '0.000000', 'showLinkBar': 'true',
                  'thickness': '0.000000', 'displayType': '1',
                  'surch2': '0.000000', 'surch1': '0.000000',
                  'mesoFollowUpGap': '0.000000', 'linkEvalAct': 'false',
                  'linkEvalSegLen': '10.000000', 'direction': 'ALL',
                  'lnChgDistIsPerLn': 'false', 'ovtSpeedFact': '1.300000',
                  'ovtOnlyPT': 'false', 'lookAheadDistOvt': '250.000000',
                  'mesoSpeed': '50.000000', 'name': '', 'level': '1',
                  'isPedArea': 'false', 'emergStopDist': '5.000000',
                  'linkBehavType': '1', 'lnChgEvalAct': 'true',
                  'vehRecAct': 'true'}
        self.assertEqual(self.links.getLink(1), answer)
        self.links.removeLink(1)
        self.assertRaises(KeyError, self.links.getLink, 1)


class input_unittest(unittest.TestCase):
    def setUp(self):
        self.v = vissim.Vissim(network)
        self.inputs = self.v.inputs

    def test_getInput(self):
        answer = {'no': '1', 'link': '3', 'name': '', 'anmFlag': 'false'}
        self.assertEqual(self.inputs.getInput('no', 1), answer)

    def test_setInput(self):
        answer = {'no': '1', 'link': '3', 'name': 'test', 'anmFlag': 'false'}
        self.assertEqual(self.inputs.setInput(1, 'name', 'test'), answer)

    def test_getVols(self):
        answer = [{'volume': '1500.000000', 'timeInt': '1 0', 'vehComp': '1',
                   'cont': 'false', 'volType': 'STOCHASTIC'}]
        self.assertEqual(self.inputs.getVols(1), answer)

    def test_addVol(self):
        answer = [{'volume': '1500.000000', 'timeInt': '1 0', 'vehComp': '1',
                   'cont': 'false', 'volType': 'STOCHASTIC'},
                  {'volume': '100', 'timeInt': '1 0', 'vehComp': '1',
                   'cont': 'false', 'volType': 'EXACT'}]
        self.assertEqual(self.inputs.addVol(1, 100), answer)

    def test_updateVol(self):
        answer = [{'volume': '1000.000000', 'timeInt': '1 0', 'vehComp': '1',
                   'cont': 'false', 'volType': 'STOCHASTIC'}]
        self.assertEqual(self.inputs.updateVol(1, 0, '1000.000000'), answer)

    def test_createInput(self):
        defaults = {'anmFlag': 'false', 'name': 'test', 'no': '6000'}
        answer = {'anmFlag': 'false', 'name': 'test', 'no': '6000',
                  'link': '1'}
        self.assertEqual(self.inputs.createInput(1, 100, **defaults), answer)

    def test_removeInput(self):
        answer = {'no': '1', 'link': '3', 'name': '', 'anmFlag': 'false'}
        self.assertEqual(self.inputs.getInput('no', 1), answer)
        self.inputs.removeInput(1)
        self.assertRaises(KeyError, self.inputs.getInput, 'no', 1)


class staticrouting_unittest(unittest.TestCase):
    def setUp(self):
        self.v = vissim.Vissim(network)
        self.routing = self.v.routing

    def test_getRouting(self):
        answer = {'name': '', 'no': '1', 'anmFlag': 'false', 'pos': '0.000000',
                  'link': '3', 'combineStaRoutDec': 'false',
                  'allVehTypes': 'false'}
        self.assertEqual(self.routing.getRouting('no', 1), answer)

    def test_setRouting(self):
        answer = {'name': '', 'no': '1', 'anmFlag': 'false',
                  'pos': '0.000000', 'link': '3',
                  'combineStaRoutDec': 'false', 'allVehTypes': 'true'}
        self.assertEqual(self.routing.setRouting(1, 'allVehTypes', 'true'),
                         answer)

    def test_getVehicleClasses(self):
        answer = [{'key': '10'}, {'key': '20'}]
        self.assertEqual(self.routing.getVehicleClasses(10), answer)

    def test_setVehicleClasses(self):
        answer = [{'key': '10'}, {'key': '20'}, {'key': '30'}, {'key': '40'}]
        classes = [30, 40]
        self.assertEqual(self.routing.setVehicleClasses(10, classes), answer)

    def test_getRoutes(self):
        answer = [{'destLink': '3', 'destPos': '383.900000', 'name': '',
                   'no': '1', 'relFlow': '2 0:64.000000'},
                  {'destLink': '1', 'destPos': '208.500000', 'name': '',
                   'no': '2', 'relFlow': '2 0:4.000000'},
                  {'destLink': '13', 'destPos': '74.400000', 'name': '',
                   'no': '3', 'relFlow': '2 0:6.000000'},
                  {'destLink': '23', 'destPos': '100.600000', 'name': '',
                   'no': '4', 'relFlow': '2 0:7.000000'},
                  {'destLink': '4', 'destPos': '336.200000', 'name': '',
                   'no': '5', 'relFlow': '2 0:17.000000'},
                  {'destLink': '10', 'destPos': '157.200000', 'name': '',
                   'no': '6', 'relFlow': '2 0:2.000000'}]
        self.assertEqual(self.routing.getRoutes(1), answer)

    def test_getRoute(self):
        answer = {'no': '1', 'destLink': '3', 'destPos': '383.900000',
                  'relFlow': '2 0:64.000000', 'name': ''}
        self.assertEqual(self.routing.getRoute(1, 'no', 1), answer)

    def test_setRoute(self):
        answer = {'no': '1', 'destLink': '3', 'destPos': '383.900000',
                  'relFlow': '2 0:64.000000', 'name': 'doggie'}
        self.assertEqual(self.routing.setRoute(1, 1, 'name', 'doggie'), answer)

    def test_updateFlow(self):
        answer = {'no': '1', 'destLink': '3', 'destPos': '383.900000',
                  'relFlow': '2 0:100', 'name': ''}
        self.assertEqual(self.routing.updateFlow(1, 1, 100), answer)

    def test_removeRouting(self):
        answer = {'name': '', 'no': '1', 'anmFlag': 'false', 'pos': '0.000000',
                  'link': '3', 'combineStaRoutDec': 'false',
                  'allVehTypes': 'false'}
        self.assertEqual(self.routing.getRouting('no', 1), answer)
        self.routing.removeRouting(1)
        self.assertRaises(KeyError, self.routing.getRouting, 'no', 1)

    def test_removeRoute(self):
        answer = {'no': '1', 'destLink': '3', 'destPos': '383.900000',
                  'relFlow': '2 0:64.000000', 'name': ''}
        self.assertEqual(self.routing.getRoute(1, 'no', 1), answer)
        self.routing.removeRoute(1, 1)
        self.assertRaises(KeyError, self.routing.getRoute, 1, 'no', 1)

    def test_getRouteSeqs(self):
        answer = [{'key': '10028'}]
        self.assertEqual(self.routing.getRouteSeqs(1, 2), answer)

    def test_addRouteSeq(self):
        answer = [{'key': '10028'}, {'key': '1029'}, {'key': '1030'}]
        self.assertEqual(self.routing.addRouteSeq(1, 2, [1029, 1030]), answer)

    def test_updateRouteSeq(self):
        answer = [{'key': '100'}]
        self.assertEqual(self.routing.updateRouteSeq(1, 2, 0, 100), answer)

    def test_createRouting(self):
        defaults = {'allVehTypes': 'false', 'anmFlag': 'false', 'no': '9999',
                    'combineStaRoutDec': 'false', 'name': '', 'pos': '0.0000',
                    'vehClasses': ['1']}
        answer = {'allVehTypes': 'false', 'anmFlag': 'false', 'no': '9999',
                  'combineStaRoutDec': 'false', 'name': '', 'pos': '0.0000',
                  'link': '10'}
        self.assertEqual(self.routing.createRouting(10, **defaults), answer)

    def test_createRoute(self):
        routingDefaults = {'allVehTypes': 'false', 'anmFlag': 'false',
                           'no': '9999', 'combineStaRoutDec': 'false',
                           'name': '', 'pos': '0.0000', 'vehClasses': ['1']}
        self.routing.createRouting(10, **routingDefaults)
        routeDefaults = {'destPos': '0.000', 'name': '', 'no': '1',
                         'relFlow': ''}
        answer = {'destPos': '0.000', 'name': '', 'no': '1', 'relFlow': '',
                  'destLink': '12'}
        self.assertEqual(self.routing.createRoute(9999, 12, **routeDefaults),
                         answer)


if __name__ == '__main__':
    v = 3
    links = unittest.TestLoader().loadTestsFromTestCase(link_unittest)
    inputs = unittest.TestLoader().loadTestsFromTestCase(input_unittest)
    routing = unittest.TestLoader().loadTestsFromTestCase(staticrouting_unittest)
    unittest.TextTestRunner(verbosity=v).run(links)
    unittest.TextTestRunner(verbosity=v).run(inputs)
    unittest.TextTestRunner(verbosity=v).run(routing)
