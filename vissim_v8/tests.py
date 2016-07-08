import unittest
import vissim_v8 as vissim

network = 'test_networks/Busmall.inpx'


class link_unittest(unittest.TestCase):
    def setUp(self):
        self.links = vissim.Links(network)

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
        self.links.removeLink(1)
        self.assertRaises(KeyError, self.links.getLink, 1)


class input_unittest(unittest.TestCase):
    def setUp(self):
        self.inputs = vissim.Inputs(network)

    def test_getInput(self):
        answer = {'no': '1', 'link': '3', 'name': '', 'anmFlag': 'false'}
        self.assertEqual(self.inputs.getInput('no', 1), answer)

    def test_setInput(self):
        answer = {'no': '1', 'link': '3', 'name': 'test', 'anmFlag': 'false'}
        self.assertEqual(self.inputs.setInput(1, 'name', 'test'), answer)

    def test_getVols(self):
        pass

    def test_setVols(self):
        pass

    def test_createInput(self):
        pass

    def test_removeInput(self):
        pass

if __name__ == '__main__':
    links = unittest.TestLoader().loadTestsFromTestCase(link_unittest)
    inputs = unittest.TestLoader().loadTestsFromTestCase(input_unittest)
    unittest.TextTestRunner(verbosity=3).run(links)
    unittest.TextTestRunner(verbosity=3).run(inputs)
