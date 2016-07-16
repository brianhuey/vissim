import unittest
import vissim_v8 as vissim

network = 'test_networks/Busmall.inpx'


class link_unittest(unittest.TestCase):
    def setUp(self):
        self.v = vissim.Vissim(network)
        self.links = self.v.links

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

    def test_getGeometry(self):
        answer = [{'y': '3786.952000', 'x': '-282.116000',
                   'zOffset': '0.000000'},
                  {'y': '4007.169000', 'x': '-285.973000',
                   'zOffset': '0.000000'}]
        self.assertEqual(self.links.getGeometry(1), answer)

    def test_setGeometry(self):
        answer = [{'y': '3786.952000', 'x': '-282.116000',
                   'zOffset': '0.000000'},
                  {'y': '4007.169000', 'x': '-285.973000',
                   'zOffset': '0.000000'},
                  {'y': '2', 'x': '1', 'zOffset': '3'}]
        self.assertEqual(self.links.setGeometry(1, [(1, 2, 3)]), answer)

    def test_getLanes(self):
        answer = [{'width': '3.500000'}, {'width': '3.500000'},
                  {'width': '3.500000'}]
        self.assertEqual(self.links.getLanes(3), answer)

    def test_setLanes(self):
        answer = [{'width': '3.500000'}, {'width': '3.500000'},
                  {'width': '3.500000'}, {'width': '3.5'}, {'width': '3.5'}]
        self.assertEqual(self.links.setLanes(3, [3.5, 3.5]), answer)

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

    def test_setVols(self):
        answer = [{'volume': '1500.000000', 'timeInt': '1 0', 'vehComp': '1',
                   'cont': 'false', 'volType': 'STOCHASTIC'},
                  {'volume': '100', 'timeInt': '1 0', 'vehComp': '1',
                   'cont': 'false', 'volType': 'EXACT'}]
        self.assertEqual(self.inputs.setVols(1, 100), answer)

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

    def test_getRoute(self):
        answer = {'no': '1', 'destLink': '3', 'destPos': '383.900000',
                  'relFlow': '2 0:64.000000', 'name': ''}
        self.assertEqual(self.routing.getRoute(1, 'no', 1), answer)

    def test_setRoute(self):
        answer = {'no': '1', 'destLink': '3', 'destPos': '383.900000',
                  'relFlow': '2 0:64.000000', 'name': 'doggie'}
        self.assertEqual(self.routing.setRoute(1, 1, 'name', 'doggie'), answer)

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

    def test_getRouteSeq(self):
        answer = [{'key': '10028'}]
        self.assertEqual(self.routing.getRouteSeq(1, 2), answer)

    def test_setRouteSeq(self):
        answer = [{'key': '10028'}, {'key': '1029'}, {'key': '1030'}]
        self.assertEqual(self.routing.setRouteSeq(1, 2, [1029, 1030]), answer)

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
