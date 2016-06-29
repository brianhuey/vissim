#!/usr/bin/env python
""" VISSIM Tools v2.0 """
from re import findall as _findall, match as _match, search as _search
from re import split as _split
from math import sqrt as _sqrt
from copy import copy as _copy


def _median(lst):
    """ Stock median function from: http://stackoverflow.
    com/questions/24101524/finding-median-of-list-in-python
    """
    lst = sorted(lst)
    if len(lst) < 1:
        return None
    if len(lst) % 2 == 1:
        return lst[((len(lst) + 1) / 2) - 1]
    else:
        return float(sum(lst[(len(lst) / 2) - 1:(len(lst) / 2) + 1])) / 2.0


def _flatten(coll):
    if isinstance(coll, list):
        return [int(a) for i in coll for a in _flatten(i)]
    else:
        return [coll]


def _importSection(obj, filename):
    """ Imports section's syntax into dictionary.
    """
    name = obj.name
    try:
        with open(filename, 'r') as data:
            section = None
            for row in data:
                found = _findall(r'(?<=\- )(.*?)(?=\: -)', row)
                if row in ['\n', '\r\n']:
                    continue
                elif found:
                    section = found[0]
                elif section == name and row[0] is not '-':
                    obj._readSection(row)
                else:
                    continue
    except IOError:
        print 'cannot open', filename


def _updateFile(orgFile, newFile, name, printData):
    """ Update a section of a VISSIM .INP file.
        Inputs: filename, object type(Inputs, Routing Decision, etc.) and list
        of strings with VISSIM syntax.
        Outputs: new file
    """
    search = '-- ' + name + ': --'
    f = open(orgFile, 'r')
    lines = f.readlines()
    f.close()
    f = open(newFile, 'w')
    startDelete = False
    print 'Writing %s to %s ...' % (name, newFile)
    for line in lines:
        if startDelete is True and line[:3] == '-- ':
            startDelete = False
            f.write('\n\n\n')
        if line[:len(search)] == search:
            startDelete = True
            for newLine in printData:
                f.write(str(newLine) + '\n')
        if startDelete is False:
            f.write(line)
    f.close()


def _exportSection(obj, filename):
    """ Prepare for export all dictionaries within a given object

        Input: Dict object
        Output: List of all items for a given class in VISSIM syntax
    """
    first_line = '-- ' + obj.name + ': --\n'
    second_line = '-' * (len(first_line) - 1) + '\n'
    print_data = [first_line + second_line]
    print 'Reading %s ...' % obj.name
    for value in obj.data.values():
        print_data += obj._output(value)
    print 'Updating %s ...' % obj.name
    _updateFile(obj.filename, filename, obj.name, print_data)


def _checkKeyData(obj, key, label):
    if key is not None:
        if key not in obj.data:
            raise KeyError('%s not a valid key for object %s' %
                           (key, obj.name))
    if label not in obj.types:
        raise KeyError('%s not a valid label for object %s' %
                       (label, obj.name))
    return True


def _getData(obj, key, label):
    """ Returns requested value from vissim object
    """
    _checkKeyData(obj, key, label)
    if key is None:
        new = obj.data[label]
    else:
        new = obj.data[key][label]
    return _copy(new)


def _setData(obj, key, label, value):
    """ Sets given value in vissim object
    """
    _checkKeyData(obj, key, label)
    if not isinstance(value, obj.types[label]):
        value = obj.types[label](value)
    if key is None:
        obj.data[label] = value
    else:
        obj.data[key][label] = value


def _updateData(obj, key, label, value, pos=None, newKey=None):
    _checkKeyData(obj, key, label)
    if key is None:
        if (isinstance(obj.data[label], list) is True) and (pos is None):
            obj.data[label].append(value)
            obj.data[label] = list(_flatten(obj.data[label]))
        elif isinstance(obj.data[label], list) and pos:
            obj.data[label].insert(pos, value)
            obj.data[label] = list(_flatten(obj.data[label]))
    else:
        if isinstance(obj.data[key][label], dict):
            obj.data[key][label][newKey] = value
        if (isinstance(obj.data[key][label], list) is True) and (pos is None):
            obj.data[label].append(value)
            obj.data[label] = list(_flatten(obj.data[label]))
        elif isinstance(obj.data[key][label], list) and pos:
            obj.data[label].insert(pos, value)
            obj.data[label] = list(_flatten(obj.data[label]))


def _convertType(iterable, newType):
    iterType = type(iterable)
    return iterType([newType(i) for i in iterable])


class Inputs:
    """ Handles Inputs section of .INP file.
    """
    def __init__(self, filename):
        self.filename = filename
        self.name = 'Inputs'
        self.data = {}
        self.currData = None
        self.types = {'composition': int, 'exact': bool, 'from': float,
                      'input': int, 'label': tuple, 'link': int, 'name': str,
                      'q': float, 'until': float}
        _importSection(self, filename)

    def get(self, inputNum, label, string=True):
        """ Get value from Input.
            Input: Input number, Value label
            Output: Value
        """
        if string:
            return str(_getData(self, inputNum, label))
        else:
            return _getData(self, inputNum, label)

    def set(self, inputNum, label, value):
        """ Set value from Input.
            Input: Input number, Value label, value
            Output: Change is made in place
        """
        _setData(self, inputNum, label, value)

    def getInputNumByLink(self, linkNum):
        """ Get value from Input by link number
            Input: Link number
            Output: Input number as key, time and composition as values
        """
        if isinstance(linkNum, str) is False:
            linkNum = str(linkNum)
        result = {k: {'from': v['from'], 'until': v['until'], 'composition':
                      v['composition']} for k, v in self.data.items()
                  if v['link'] == linkNum}
        if len(result) == 0:
            raise KeyError('%s not in data' % (linkNum))
        else:
            return result

    def create(self, linkNum, demand, comp, **kwargs):
        if self.data.keys():
            num = max(self.data.keys()) + 1
        else:
            num = 1
        inputNum = kwargs.get('input', num)
        self.data[inputNum] = {}
        self.set(inputNum, 'input', inputNum)
        self.set(inputNum, 'q', demand)
        self.set(inputNum, 'link', linkNum)
        self.set(inputNum, 'composition', comp)
        # Default values
        self.set(inputNum, 'name', kwargs.get('name', '""'))
        self.set(inputNum, 'label', kwargs.get('label', ('0.00', '0.00')))
        self.set(inputNum, 'from', kwargs.get('from', '0.0'))
        self.set(inputNum, 'until', kwargs.get('until', '3600.0'))
        self.set(inputNum, 'exact', kwargs.get('exact', False))

    def _readSection(self, line):
        """ Process the Input section of the INP file.
        """
        if _match('^INPUT\s+\d+', line):
            inputNum = self.types['input'](_findall('INPUT\s+(\d+)', line)[0])
            self.currData = {'input': inputNum}
        elif _match('^\s+NAME', line):
            self.currData['name'] = _findall('NAME\s+(".+"|"")', line)[0]
            self.currData['label'] = _findall('LABEL\s+(-?\d+.\d+)\s(-?\d+.\d+)', line)[0]
        elif _match('^\s+LINK', line):
            self.currData['link'] = _findall('LINK\s+(\d+)', line)[0]
            if _search('EXACT', line):
                self.currData['exact'] = True
                self.currData['q'] = _findall('Q EXACT (.+) COMPOSITION',
                                              line)[0]
            else:
                self.currData['exact'] = False
                self.currData['q'] = _findall('Q (.+) COMPOSITION', line)[0]
            self.currData['composition'] = _findall('COMPOSITION (\d)',
                                                    line)[0]
        elif _match('^\s+TIME', line):
            self.currData['from'] = _findall('FROM (\d+.\d+)', line)[0]
            self.currData['until'] = _findall('UNTIL (\d+.\d+)', line)[0]
            # Last line, create Input object
            self.create(self.currData['link'], self.currData['q'],
                        self.currData['composition'], **self.currData)
        else:
            print 'Non-Input data provided: %s' % line

    def _output(self, inputs):
        """ Outputs Inputs syntax to VISSIM.

        Input: A single Inputs dictionary
        Output: Inputs back into VISSIM syntax
        """
        vissimOut = []
        inputNum = inputs['input']

        def _out(label, s=True):
            return self.get(inputNum, label, string=s)
        vissimOut.append('INPUT ' + _out('input').rjust(6))
        vissimOut.append('NAME '.rjust(10) + _out('name') + ' LABEL  ' +
                         _out('label', s=False)[0] + ' ' +
                         _out('label', s=False)[1])
        if _out('exact', s=False) is True:
            vissimOut.append('LINK '.rjust(10) + _out('link') + ' Q EXACT ' +
                             _out('q') + ' COMPOSITION ' +
                             _out('composition'))
        else:
            vissimOut.append('LINK '.rjust(10) + _out('link') + ' Q ' +
                             _out('q') + ' COMPOSITION ' + _out('composition'))
        vissimOut.append('TIME FROM '.rjust(15) + _out('from') + ' UNTIL ' +
                         _out('until'))
        return vissimOut

    def export(self, filename):
        """ Prepare for export all inputs in a given inputs object

            Input: Inputs object
            Output: List of all inputs in VISSIM syntax
        """
        _exportSection(self, filename)

    def updateInput(self, link, timeFrom, timeUntil, composition, demand):
        """ Update demand values for a given link, time period and composition
        """
        compareDict = {'link': link, 'from': timeFrom, 'until': timeUntil,
                       'composition': composition}
        for inp in self.data.values():
            if {key: inp[key] for key in compareDict.keys()} == compareDict:
                inp['q'] = demand


class Links:
    """ Handles Links section of .INP file.
    """
    def __init__(self, filename):
        self.filename = filename
        self.name = 'Links'
        self.data = {}
        self.over = None
        self.currData = None
        self.closed = None
        self.types = {'link': int, 'name': str, 'label': tuple,
                      'behaviortype': int, 'displaytype': int, 'length': float,
                      'lanes': int, 'lane_width': list, 'gradient': float,
                      'cost': float, 'surcharges': list,
                      'segment_length': float, 'evaluation': bool,
                      'from': list, 'over': list, 'to': list, 'closed': dict}
        _importSection(self, filename)

    def get(self, linkNum, label, string=True):
        """ Get value from Link.
            Input: Link number, Value label
            Output: Value
        """
        if string:
            return str(_getData(self, linkNum, label))
        else:
            return _getData(self, linkNum, label)

    def set(self, linkNum, label, value):
        """ Set value from Link.
            Input: Link number, Value label, value
            Output: Change is made in place
        """
        _setData(self, linkNum, label, value)

    def create(self, coordFrom, coordTo, **kwargs):
        if self.data.keys():
            num = max(self.data.keys()) + 1
        else:
            num = 1
        linkNum = kwargs.get('link', num)
        self.data[linkNum] = {}
        self.set(linkNum, 'link', linkNum)
        self.set(linkNum, 'from', coordFrom)
        self.set(linkNum, 'to', coordTo)
        # Default values
        self.set(linkNum, 'name', kwargs.get('name', '""'))
        self.set(linkNum, 'behaviortype', kwargs.get('behaviortype', 1))
        self.set(linkNum, 'cost', kwargs.get('cost', 0.00000))
        self.set(linkNum, 'displaytype', kwargs.get('displaytype', 1))
        self.set(linkNum, 'gradient', kwargs.get('gradient', 0.00000))
        self.set(linkNum, 'label', kwargs.get('label', ('0.00', '0.00')))
        self.set(linkNum, 'lane_width', kwargs.get('lane_width', [3.66]))
        self.set(linkNum, 'lanes', kwargs.get('lanes', 1))
        self.set(linkNum, 'segment_length', kwargs.get('segment_length',
                 10.000))
        self.set(linkNum, 'surcharges', kwargs.get('surcharges',
                 [0.00000, 0.00000]))
        self.set(linkNum, 'evaluation', kwargs.get('evaluation', False))
        self.set(linkNum, 'over', kwargs.get('over', []))
        self.set(linkNum, 'length', kwargs.get('length', 0))
        if self.get(linkNum, 'over') and self.get(linkNum, 'length') == 0:
            x1, y1 = self.get(linkNum, 'from')
            z1 = 0
            length = 0
            for coord in self.get(linkNum, 'over'):
                x2, y2, z2 = _convertType(coord, float)
                dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
                length += _sqrt(dx**2 + dy**2 + dz**2)
                x1, y1, z1 = x2, y2, z2
            self.set(linkNum, 'length', round(length, 3))
        elif self.get(linkNum, 'length') == 0:
            length = round(_sqrt((self.get(linkNum, 'to')[0] -
                           self.get(linkNum, 'from')[0])**2 +
                           (self.get(linkNum, 'to'[1] - self.get(linkNum,
                            'from')[1])**2), 3))
            self.set(linkNum, 'length', length)

    def _readSection(self, line):
        if _match('^LINK', line):
            linkNum = (self.types['link'](_findall('LINK\s+(\d+)', line)[0]))
            self.currData = {'link': linkNum}
            self.currData['name'] = _findall('NAME\s+(".+"|"")', line)[0]
            self.currData['label'] = (_findall(
                                      'LABEL\s+(-?\d+.\d+)\s(-?\d+.\d+)',
                                      line)[0])
        elif _match('^\s+BEHAVIORTYPE', line):
            self.currData['behaviortype'] = _findall('BEHAVIORTYPE\s+(\d+)',
                                                     line)[0]
            self.currData['displaytype'] = _findall('DISPLAYTYPE\s+(\d+)',
                                                    line)[0]
        elif _match('^\s+LENGTH', line):
            self.currData['length'] = _findall('LENGTH\s+(\d+.\d+)', line)[0]
            self.currData['lanes'] = _findall('LANES\s+(\d)', line)[0]
            width = _findall('LANE_WIDTH\s+(.+)\s+GRADIENT', line)[0]
            self.currData['lane_width'] = _split('\s+', width)
            self.currData['gradient'] = _findall('GRADIENT\s+(-?\d+.\d+)',
                                                 line)[0]
            self.currData['cost'] = _findall('COST\s+(\d+.\d+)', line)[0]
            self.currData['surcharges'] = _findall('SURCHARGE\s+(\d+.\d+)',
                                                   line)
            self.currData['segment_length'] = (_findall(
                                               'SEGMENT LENGTH\s+(\d+.\d+)',
                                               line)[0])
            if _search('EVALUATION', line):
                self.currData['evaluation'] = True
            else:
                self.currData['evaluation'] = False
        elif _match('^\s+FROM', line):
            self.currData['from'] = _findall('(-?\d+.\d+)', line)
        elif _match('^\s+OVER', line):
            if 'over' not in self.currData:
                self.currData['over'] = []
            self.currData['over'] += _findall('OVER (-?\d+.\d+) (-?\d+.\d+) (-?\d+.\d+)', line)
        elif _match('^\s+TO', line):
            self.currData['to'] = _findall('(-?\d+.\d+)', line)
            self.create(self.currData['from'], self.currData['to'], **self.currData)
        elif _match('^\s+CLOSED', line):
            self.currData['closed'] = {}
        elif 'closed' in self.currData and _match('^LANE', line):
            lane = _findall('^LANE\s+(\d+)', line)
            veh_classes = _findall('VEHICLE_CLASSES (.+)', line)
            self.currData['closed'][lane] = _split('\s', veh_classes)
            self.set(self.currData['link'], 'closed', self.currData['closed'])
        else:
            print 'Non-link data provided: %s' % line

    def _output(self, links):
        """ Outputs Links syntax to VISSIM.

        Input: A single links dictionary
        Output: Route decisions back into VISSIM syntax
        """
        vissimOut = []
        linkNum = links['link']

        def _out(label, s=True):
            return self.get(linkNum, label, string=s)
        vissimOut.append('LINK ' + _out('link').rjust(6) + ' NAME ' +
                         _out('name') + ' LABEL ' +
                         _out('label', s=False)[0] + ' ' +
                         _out('label', s=False)[1])
        vissimOut.append('BEHAVIORTYPE '.rjust(15) + _out('behaviortype').
                         rjust(5) + ' DISPLAYTYPE' + _out('displaytype').
                         rjust(5))
        laneWidth = ''
        if len(_out('lane_width', s=False)) > 1:
            for width in _out('lane_width', s=False):
                laneWidth += width.rjust(5)
        else:
            laneWidth = _out('lane_width', s=False)[0].rjust(5)
        evaluation = 'EVALUATION' if _out('evaluation', s=False) else ''
        vissimOut.append('LENGTH '.rjust(9) + _out('length').rjust(8) +
                         ' LANES ' + _out('lanes').rjust(2) +
                         ' LANE_WIDTH ' + laneWidth + ' GRADIENT ' +
                         _out('gradient').ljust(10) + ' COST ' +
                         _out('cost').ljust(7) + ' SURCHARGE ' +
                         _out('surcharges', s=False)[0] + ' SURCHARGE ' +
                         _out('surcharges', s=False)[1] + ' SEGMENT LENGTH ' +
                         _out('segment_length').rjust(8) +
                         evaluation)
        vissimOut.append('FROM '.rjust(7) + _out('from', s=False)[0] + ' ' +
                         _out('from', s=False)[1])
        if _out('over', s=False):
            overStr = ''
            for i in _out('over', s=False):
                overStr += '  OVER ' + i[0] + ' ' + i[1] + ' ' + i[2]
            vissimOut.append(overStr)
        vissimOut.append('TO '.rjust(5) + _out('to', s=False)[0].rjust(10) +
                         ' ' + _out('to', s=False)[1])
        return vissimOut

    def export(self, filename):
        """ Prepare for export all links in a given links object

            Input: Links object
            Output: List of all links in VISSIM syntax
        """
        _exportSection(self, filename)


class Connector:
    """ Handles Connector section of .INP file.
    """
    def __init__(self, filename):
        self.filename = filename
        self.name = 'Connectors'
        self.data = {}
        self.currData = None
        self.curr_lane = None
        _importSection(self, filename)
        self.links = Links(self.filename)

    def _readSection(self, line):
        if _match('^CONNECTOR', line):
            # Connector number is dictionary key
            conn = _findall('^CONNECTOR\s+(\d+)', line)[0]
            self.data[conn] = {}
            self.currData = self.data[conn]
            self.currData['connector'] = conn
            self.currData['name'] = _findall('NAME\s+(".+"|"")', line)[0]
            self.currData['label'] = _findall('LABEL\s+(-?\d+.\d+)\s(-?\d+.\d+)', line)[0]
        elif _match('^\s+FROM', line):
            self.currData['from'] = _findall('LINK\s+(\d+)', line)[0]
            lanes = _findall('LANES\s(.+)\sAT', line)[0]
            self.currData['from_lanes'] = _split('\s+', lanes)
            self.currData['from_at'] = _findall('AT\s+(\d+.\d+)', line)[0]
        elif _match('^\s+OVER', line):
            if 'over' not in self.currData:
                self.currData['over'] = []
            self.currData['over'] += _findall('OVER (-?\d+.\d+) (-?\d+.\d+) (-?\d+.\d+)', line)
        elif _match('^\s+TO', line):
            self.currData['to'] = _findall('LINK\s+(\d+)', line)[0]
            lanes = _findall('LANES\s(.+)\sAT', line)[0]
            self.currData['to_lanes'] = _split('\s+', lanes)
            self.currData['to_at'] = _findall('AT\s+(\d+.\d+)', line)[0]
            self.currData['behaviortype'] = _findall('BEHAVIORTYPE\s+(\d+)', line)[0]
            self.currData['displaytype'] = _findall('DISPLAYTYPE\s+(\d+)', line)[0]
        elif _match('^\s+DX_EMERG_STOP', line):
            self.currData['dx_emerg_stop'] = _findall('DX_EMERG_STOP\s+(\d+.\d+)', line)[0]
            self.currData['dx_lane_change'] = _findall('DX_LANE_CHANGE\s+(\d+.\d+)', line)[0]
        elif _match('^\s+GRADIENT', line):
            self.currData['gradient'] = _findall('GRADIENT\s+(-?\d+.\d+)',
                                                  line)[0]
            self.currData['cost'] = _findall('COST\s+(\d+.\d+)', line)[0]
            self.currData['surcharges'] = _findall('SURCHARGE\s+(\d+.\d+)',
                                                    line)
        elif _match('^\s+SEGMENT', line):
            self.currData['segment_length'] = _findall('LENGTH\s+(\d+.\d+)',
                                                        line)[0]
            if _search('NONE ANIMATION', line):
                self.currData['visualization'] = False
            else:
                self.currData['visualization'] = True
        elif _search('NOLANECHANGE', line):
            self.currData['nolanechange'] = {}
            lanes = _findall('LANE\s+(\d+) (\w+) (\w+)', line)
            for lane, o, d in lanes:
                self.currData['nolanechange'][lane] = {'from': o, 'to': d}
        else:
            print 'Non-connector data provided: %s' % line

    def _output(self, connector):
        """ Outputs connector syntax to VISSIM.

        Input: A single connector dictionary
        Output: connector back into VISSIM syntax
        """
        vissimOut = []
        vissimOut.append('CONNECTOR ' + str(connector['connector']) +
                          ' NAME ' + connector['name'] + ' LABEL ' +
                          connector['label'][0] + ' ' + connector['label'][1])
        from_lanes_str = ''
        for i in connector['from_lanes']:
            from_lanes_str += i + ' '
        vissimOut.append('FROM LINK '.rjust(12) + str(connector['from']) +
                          ' LANES ' + from_lanes_str + 'AT ' + connector
                          ['from_at'])
        over_str = ''
        for i in connector['over']:
            over_str += '  OVER ' + i[0] + ' ' + i[1] + ' ' + i[2]
        vissimOut.append(over_str)
        to_lanes_str = ''
        for i in connector['to_lanes']:
            to_lanes_str += i + ' '
        vissimOut.append('TO LINK '.rjust(10) + str(connector['to']) +
                          ' LANES '.rjust(7) + to_lanes_str + 'AT ' + connector
                          ['to_at'].ljust(6) + ' BEHAVIORTYPE ' + connector
                          ['behaviortype'] + ' DISPLAYTYPE ' + connector
                          ['displaytype'] + ' ALL')
        vissimOut.append('DX_EMERG_STOP '.rjust(16) + connector
                          ['dx_emerg_stop'] + ' DX_LANE_CHANGE ' + connector
                          ['dx_lane_change'])
        vissimOut.append('GRADIENT '.rjust(11) + connector['gradient'] +
                          ' COST ' + connector['cost'] + ' SURCHARGE ' +
                          connector['surcharges'][0] + ' SURCHARGE ' +
                          connector['surcharges'][1])
        if connector['visualization'] is False:
            vissimOut.append('SEGMENT LENGTH '.rjust(17) + connector
                              ['segment_length'] + ' NONE ANIMATION')
        else:
            vissimOut.append('SEGMENT LENGTH '.rjust(17) + connector
                              ['segment_length'] + ' ANIMATION')
        return vissimOut

    def export(self, filename):
        """ Prepare for export all connector lots in a given connector object

            Input: connector object
            Output: List of all connector lots in VISSIM syntax
        """
        _exportSection(self, filename)

    def create(self, from_link, to_link, **kwargs):
        connector_num = str(self.data.get('num', max(self.data.keys()) + 1))
        self.data[connector_num] = {}
        connector = self.data[connector_num]
        connector['connector'] = connector_num
        connector['from'] = from_link
        connector['to'] = to_link
        # Default values
        connector['label'] = kwargs.get('label', ('0.00', '0.00'))
        connector['from_lanes'] = kwargs.get('from_lanes', '1')
        connector['from_at'] = kwargs.get('from_at', self.links.get(from_link,
                                          'length'))
        # Calculate default spline points between from link and to link:
        over1 = self.links.get(from_link, 'to').append('0.000')
        over4 = self.links.get(to_link, 'from').append('0.000')
        if over4[0] == over1[0] and over4[1] == over1[1]:
            over1[1] = str(float(over1[1]) + 0.001)
            over2 = [str(float(over4[0]) + 0.001), over4[1], over4[2]]
            over3 = [str(_median([over2[0], over4[0]])), str(_median([over2[1],
                     over4[1]])), str(_median([over2[2], over4[2]]))]
        else:
            over2 = [str(_median([over4[0], over1[0]])), str(_median([over4[1],
                     over1[1]])), str(_median([over4[2], over1[2]]))]
            over3 = [str(_median([over2[0], over4[0]])), str(_median([over2[1],
                     over4[1]])), str(_median([over2[2], over4[2]]))]
        connector['over'] = kwargs.get('over', [over1, over2, over3, over4])
        connector['name'] = kwargs.get('name', '""')
        connector['to_lanes'] = kwargs.get('to_lanes', ['1'])
        connector['to_at'] = kwargs.get('to_at', '0.000')
        connector['behaviortype'] = kwargs.get('behaviortype', '1')
        connector['displaytype'] = kwargs.get('displaytype', '1')
        connector['dx_emerg_stop'] = kwargs.get('dx_emerg_stop', '4.999')
        connector['dx_lane_change'] = kwargs.get('dx_lane_change', '200.010')
        connector['gradient'] = kwargs.get('gradient', '0.00000')
        connector['cost'] = kwargs.get('cost', '0.00000')
        connector['surcharges'] = kwargs.get('surcharges',
                                             ['0.00000', '0.00000'])
        connector['segment_length'] = kwargs.get('segment_length', '10.000')
        connector['visualization'] = kwargs.get('visualization', True)

    def get(self, connnum, label):
        """ Get value from Connector.
            Input: Connector number, Value label
            Output: Value
        """
        return _getData(self.data, connnum, label)

    def set(self, connnum, label, value):
        """ Set value from Connector.
            Input: Connector number, Value label, value
            Output: Change is made in place
        """
        _setData(self.data, connnum, label, value)


class Parking:
    """ Handles Parking section of .INP file.
    """
    def __init__(self, filename):
        self.filename = filename
        self.name = 'Parking Lots'
        self.data = {}
        self.currData = None
        _importSection(self, filename)

    def _readSection(self, line):
        if _match('^\s+PARKING_LOT', line):
            # Parking lot number is dictionary key
            parking = _findall('PARKING_LOT\s+(\d+)')[0]
            self.data[parking] = {}
            self.currData = self.data[parking]
            self.currData['parking'] = parking
            self.currData['name'] = _findall('NAME\s+(".+"|"")', line)[0]
            self.currData['label'] = _findall('LABEL\s+(-?\d+.\d+)\s(-?\d+.\d+)', line)[0]
        elif _match('^\s+PARKING_SPACES', line):
            self.currData['spaces_length'] = _findall('LENGTH\s+(\d+.\d+)', line)[0]
        elif _match('^\s+ZONES', line):
            self.currData['zones'] = _findall('ZONES\s+(\d+)', line)[0]
            self.currData['fraction'] = _findall('FRACTION\s+(\d+.\d+), line')[0]
        elif _match('^\s+POSITION', line):
            self.currData['position_link'] = _findall('POSITION LINK\s+(\d+)', line)[0]
            self.currData['at'] = _findall('AT\s+(\d+.\d+)', line)[0]
            if _match('POSITION LINK \d+ LANE \d+', line):
                self.currData['lane'] = _findall('LANE (\d+)', line)[0]
        elif _match('^\s+LENGTH', line):
            self.currData['length'] = _findall('LENGTH\s+(\d+.\d+)', line)[0]
        elif _match('^\s+CAPACITY', line):
            self.currData['capacity'] = _findall('CAPACITY\s+(\d+)', line)[0]
        elif _match('^\s+OCCUPANCY', line):
            self.currData['occupancy'] = _findall('OCCUPANCY\s+(\d+)', line)[0]
        elif _match('^\s+DEFAULT', line):
            self.currData['desired_speed'] = _findall('DESIRED_SPEED\s+(\d+)', line)[0]
        elif _match('^\s+OPEN_HOURS', line):
            self.currData['open_hours'] = _findall('FROM\s+(\d+)\s+UNTIL\s+(\d+)', line)
        elif _match('^\s+MAX_TIME', line):
            self.currData['max_time'] = _findall('MAX_TIME\s+(\d+)', line)[0]
        elif _match('^\s+FLAT_FEE', line):
            self.currData['flat_fee'] = _findall('FLAT_FEE\s+(\d+.\d+)', line)[0]
        elif _match('^\s+FEE_PER_HOUR', line):
            self.currData['fee_per_hour'] = _findall('FEE_PER_HOUR\s+(\d+.\d+)', line)[0]
        elif _match('^\s+ATTRACTION', line):
            if 'spaces_length' in self.currData:
                self.currData['attraction'] = _findall('ATTRACTION\s+(\d+.\d+)\s(\d+.\d+)', line)
            else:
                self.currData['attraction'] = _findall('ATTRACTION\s+(\d+.\d+)', line)
        elif _match('^\s+COMPOSITION', line):
            self.currData['composition'] = _findall('COMPOSITION\s+(\d+)', line)[0]
        else:
            print 'Non-parking data provided: %s' % line

    def _output(self, parking):
        """ Outputs Parking syntax to VISSIM.

        Input: A single parking dictionary
        Output: Parking back into VISSIM syntax
        """
        vissimOut = []
        vissimOut.append('PARKING_LOT ' + str(parking['parking']) + ' NAME ' +
                          parking['name'] + ' LABEL ' + parking['label'][0] +
                          ' ' + parking['label'][1])
        if 'spaces_length' in parking:
            vissimOut.append('PARKING_SPACES LENGTH '.rjust(24) + parking
                              ['spaces_length'])
        vissimOut.append('ZONES '.rjust(8) + parking['zones'].rjust(6) +
                          ' FRACTION ' + parking['fraction'].rjust(7))
        if 'lane' in parking:
            vissimOut.append('POSITION LINK '.rjust(16) + str(parking[
                              'position_link']) + ' LANE ' + str(parking
                              ['lane']) + ' AT ' + str(parking['at']))
        else:
            vissimOut.append('POSITION LINK '.rjust(16) + str(parking
                              ['position_link']) + ' AT ' + str(parking['at']))
        vissimOut.append('LENGTH '.rjust(9) + str(parking['length']).rjust(9))
        vissimOut.append('CAPACITY   '.rjust(13) + parking['capacity'])
        vissimOut.append('OCCUPANCY '.rjust(12) + parking['occupancy'])
        vissimOut.append('DEFAULT DESIRED_SPEED '.rjust(24) + parking
                          ['desired_speed'])
        vissimOut.append('OPEN_HOURS  FROM '.rjust(19) + parking['open_hours']
                          [0].ljust(2) + ' UNTIL ' + parking['open_hours'][1])
        vissimOut.append('MAX_TIME '.rjust(11) + parking['max_time'])
        vissimOut.append('FLAT_FEE '.rjust(11) + parking['flat_fee'])
        vissimOut.append('FEE_PER_HOUR '.rjust(15) + parking['fee_per_hour'])
        if len(parking['attraction']) > 1:
            vissimOut.append('ATTRACTION '.rjust(13) +
                              parking['attraction'][0] + ' ' +
                              parking['attraction'][1])
        else:
            vissimOut.append('ATTRACTION '.rjust(13) +
                              parking['attraction'][0])
        if 'composition' in parking:
            vissimOut.append('COMPOSITION '.rjust(14) + parking
                              ['composition'])
        return vissimOut

    def __export(self, filename):
        """ Prepare for export all parking lots in a given parking object

            Input: Parking object
            Output: List of all parking lots in VISSIM syntax
        """
        _exportSection(self, filename)

    def create(self, linksobj, link, length, at, lane, **kwargs):
        parking_num = int(kwargs.get('num', max(self.data.keys())+1))
        self.data[parking_num] = {}
        parking = self.data[parking_num]
        parking['parking'] = parking_num
        parking['lane'] = lane
        parking['at'] = at
        parking['position_link'] = link
        parking['length'] = length
        # Default values
        parking['name'] = kwargs.get('name', '""')
        parking['label'] = kwargs.get('label', ['0.000', '0.000'])
        parking['spaces_length'] = kwargs.get('spaces_length', '6.000')
        parking['zones'] = kwargs.get('zones', '""')
        parking['fraction'] = kwargs.get('fraction', '1.000')
        parking['capacity'] = kwargs.get('capacity', '100')
        parking['occupancy'] = kwargs.get('occupancy', '0')
        parking['desired_speed'] = kwargs.get('desired_speed', '999')
        parking['open_hours'] = kwargs.get('open_hours', ('0', '99999'))
        parking['max_time'] = kwargs.get('max_time', '99999')
        parking['flat_fee'] = kwargs.get('flat_fee', '0.0')
        parking['fee_per_hour'] = kwargs.get('fee_per_hour', '0.0')
        parking['attraction'] = kwargs.get('attraction', '0.0 0.0')
        parking['composition'] = kwargs.get('composition', '1')


class Transit:
    """ Handles Transit section of .INP file.
    """
    def __init__(self, filename):
        self.filename = filename
        self.name = 'Public Transport'
        self.data = {}
        self.currData = None
        _importSection(self, filename)

    def _readSection(self, line):
        """ Process the Transit Decision section of the INP file
        """
        if line[0] == "LINE":
            # Dictionary key is the line number
            self.data[line[1]] = {}
            self.currData = self.data[line[1]]
            self.currData['line'] = line[1]
            self.currData['name'] = line[3]
            self.currData['route'] = line[7]
            self.currData['priority'] = line[9]
            self.currData['length'] = line[11]
            self.currData['mdn'] = line[13]
            if len(line) == 14:
                self.currData['pt'] = True
        elif line[0] == "ANM_ID":
            self.currData['link'] = line[4]
            self.currData['desired_speed'] = line[6]
            self.currData['vehicle_type'] = line[8]
        elif line[0] == "COLOR":
            self.currData['color'] = line[1]
            self.currData['time_offset'] = line[3]
        elif line[0] == "DESTINATION":
            self.currData['destination_link'] = line[2]
            self.currData['at'] = line[4]
        elif line[0] == "START_TIMES":
            self.currData['start_times'] = []
            num = (len(line)-1)/5
            for i in range(num):
                self.currData['start_times'].append([line[1+(5*i)], line
                                                     [3+(5*i)], line[5+(5*i)]])
        elif line[1] == "COURSE":
            num = (len(line)/5)
            for i in range(num):
                self.currData['start_times'].append([line[(5*i)], line
                                                     [2+(5*i)], line[4+(5*i)]])
        else:
            print 'Non-transit data provided: %s' % line

    def _output(self, transit):
        """ Outputs transit Decision syntax to VISSIM.

        Input: A single transit decision dictionary
        Output: transit decisions back into VISSIM syntax
        """
        vissimOut = []
        pt = ''
        if transit['pt'] == True:
            pt = ' PT_TELE'
        vissimOut.append(str('LINE ' + transit['line'].rjust(4) + ' NAME ' +
                              transit['name'] + '  LINE ' + transit['line'].
                              rjust(3) + '  ROUTE ' + transit['route'].rjust(3)
                              + '    PRIORITY ' + transit['priority'] +
                              '  LENGTH ' + transit['length'] + '  MDN ' +
                              transit['mdn']) + pt + '\n')
        vissimOut.append(str('ANM_ID '.rjust(12) + transit['anm'] +
                              ' SOURCE    LINK ' + transit['link'] +
                              ' DESIRED_SPEED ' + transit['desired_speed'] +
                              ' VEHICLE_TYPE ' + transit['vehicle_type']))
        vissimOut.append(str('COLOR '.rjust(24) + transit['color'] +
                              ' TIME_OFFSET ' + transit['time_offset'].
                              rjust(6)))
        vissimOut.append(str('DESTINATION    LINK '.rjust(32) + transit
                              ['destination_link'] + ' AT ' + transit['at'].
                              rjust(8)))
        time_str = 'START_TIMES '.rjust(24)
        count = 1
        for i in transit['start_times']:
            time_str += str(i[0] + ' COURSE ' + i[1] + ' OCCUPANCY ' + i[2] +
                            ' ')
            if count % 5 == 0:
                time_str += '\n'
            count += 1
        if len(transit['start_times']) > 0:
            vissimOut.append(time_str)
        return vissimOut

    def export(self, filename):
        """ Prepare for export all transit routes in a given transit object

            Input: transit object
            Output: List of all transit lots in VISSIM syntax
        """
        _exportSection(self, filename)

    def create(self, link, dest_link, at, desired_speed, vehicle_type,
               **kwargs):
        transit_num = kwargs.get('num', max(self.data.keys() or [0]) + 1)
        self.data[transit_num] = {}
        transit = self.data[transit_num]
        transit['line'] = str(transit_num)
        transit['link'] = str(link)
        transit['at'] = str(at)
        transit['destination_link'] = str(dest_link)
        transit['desired_speed'] = str(desired_speed)
        transit['vehicle_type'] = str(vehicle_type)
        # Default values
        transit['anm'] = kwargs.get('anm', '""')
        transit['name'] = kwargs.get('name', '""')
        transit['route'] = kwargs.get('route', '0')
        transit['priority'] = kwargs.get('priority', '0')
        transit['length'] = kwargs.get('length', '0')
        transit['mdn'] = kwargs.get('mdn', '0')
        transit['pt'] = kwargs.get('pt', False)
        transit['color'] = kwargs.get('color', 'CYAN')
        transit['time_offset'] = kwargs.get('time_offset', '0.0')
        transit['start_times'] = kwargs.get('start_times', [])


class Routing:
    """ Handles Routing Decision section of .INP file.
    """
    def __init__(self, filename):
        self.filename = filename
        self.name = 'Routing Decisions'
        self.data = {}
        self.currData = None
        self.destinationLink = None
        self.atLink = None
        self.currRouteNum = None
        self.currRoute = None
        self.over = None
        self.types = {'name': str, 'route': dict, 'number': int,
                      'label': tuple, 'link': int, 'at': float, 'time': list,
                      'vehicle_classes': int, 'PT': int, 'alternatives': bool}
        _importSection(self, filename)

    class Route:
        """ Individual routes within a given Route Decisions
        """
        def __init__(self, routeNum, destinationLink, atLink, fraction):
            self.name = 'Route'
            self.number = routeNum
            self.types = {'at': float, 'fraction': list, 'link': int,
                          'number': int, 'over': list}
            self.data = {'number': self.types['number'](routeNum),
                         'link': self.types['link'](destinationLink),
                         'at': self.types['at'](atLink),
                         'fraction': self.types['fraction'](fraction)}

        def get(self, label, string=True):
            """ Get value from Route.
                Input: Route number, Value label
                Output: Value
            """
            if string:
                return str(_getData(self, None, label))
            else:
                return _getData(self, None, label)

        def set(self, label, value):
            """ Set value from Route.
                Input: Route number, Value label, value
                Output: Change is made in place
            """
            _setData(self, None, label, value)

        def update(self, label, value, pos=None):
            """ Update list with new value.
                Input: label and value
                Output: Value is appended to data
            """
            _updateData(self, None, label, value, pos=pos)

        def output(self):
            """ Outputs Route syntax to VISSIM.
            """
            vissimOut = []
            routeNum = self.data['number']

            def _out(label, s=True):
                return self.get(label, string=s)
            vissimOut.append('ROUTE '.rjust(11) + _out('number').rjust(6) +
                             ' DESTINATION LINK' + _out('link').rjust(6) +
                             ' AT' + _out('at').rjust(9))
            fractionStr = ''
            for j in _out('fraction', s=False):
                fractionStr += 'FRACTION '.rjust(16) + j
            vissimOut.append(fractionStr)
            # Sometimes the route ends on the same link it began:
            if not _out('over', s=False):
                return vissimOut
            else:
                for count, j in enumerate(_out('over', s=False)):
                    if count == 0:
                        overStr = 'OVER '.rjust(12)
                        overStr += str(j)
                    elif count == len(_out('over', s=False)) - 1:
                        overStr += str(j).rjust(6)
                        vissimOut.append(overStr)
                        break
                    elif (count + 1 % 10) == 0:
                        overStr += str(j).rjust(6)
                        vissimOut.append(overStr)
                        overStr = ' ' * 11
                    else:
                        overStr += str(j).rjust(6)
                    if len(_out('over', s=False)) == 1:
                        vissimOut.append(overStr)
                return vissimOut

    def getRoute(self, decnum, routenum=None):
        """ Get route objects from a given routing decision number.
            Input: Routing decision number, route number (optional)
            Output: If route number is given, return the route object,
            otherwise return all route objects for the given decision.
        """
        if isinstance(routenum, str) is False:
            routenum = str(routenum)
        if isinstance(decnum, str) is False:
            decnum = str(decnum)
        if routenum is None:
            _getData(self.data, decnum, 'route').keys()
        elif decnum not in self.data:
            raise KeyError('%s not in data' % (decnum))
        elif routenum not in self.data[decnum]:
            raise KeyError('%s not in routing decision' % (routenum))
        else:
            return self.data[decnum]['route'][routenum]

    def get(self, decNum, label, string=True):
        """ Get value from Routing data.
            Input: Routing decision number, Value label
            Output: Value
        """
        if string:
            return str(_getData(self, decNum, label))
        else:
            return _getData(self, decNum, label)

    def set(self, decNum, label, value):
        """ Set value from Routing data.
            Input: Routing decision number, Value label, value
            Output: Change is made in place
        """
        _setData(self, decNum, label, value)

    def update(self, decNum, label, key, value):
        """ Update dict with new key and value.
            Input: Routing decision number, key, value
            Output: Change is made in place
        """
        _updateData(self, decNum, label, value, newKey=key)

    def create(self, startLink, startAt, vehClass, **kwargs):
        if self.data.keys():
            num = max(self.data.keys()) + 1
        else:
            num = 1
        decNum = kwargs.get('number', num)
        self.data[decNum] = {}
        self.set(decNum, 'number', decNum)
        self.set(decNum, 'link', startLink)
        self.set(decNum, 'at', startAt)
        self.set(decNum, 'vehicle_classes', vehClass)
        # Default values
        self.set(decNum, 'name', kwargs.get('name', '""'))
        self.set(decNum, 'label', kwargs.get('label', ('0.00', '0.00')))
        self.set(decNum, 'time', kwargs.get('time', [0.0000, 99999.0000]))
        self.set(decNum, 'route', kwargs.get('route', {}))
        self.set(decNum, 'alternatives', kwargs.get('alternatives', False))

    def _readSection(self, line):
        """ Process the Route Decision section of the INP file
        """
        if _match('^ROUTING_DECISION', line):
            # Reset from previous routes
            self.currRoute = None
            decNum = (self.types['number'](_findall(
                      'ROUTING_DECISION\s+(\d+)', line)[0]))
            # Routing decision number is dict key
            self.currData = {'number': decNum, 'route': {}}
            self.currData['name'] = _findall('NAME\s+(".+"|"")', line)[0]
            self.currData['label'] = _findall('LABEL\s+(-?\d+.\d+)\s(-?\d+.\d+)', line)[0]
        elif _match('^\s+LINK', line):
            self.currData['link'] = _findall('LINK\s+(\d+)', line)[0]
            self.currData['at'] = _findall('AT\s+(\d+.\d+)', line)[0]
        elif _match('^\s+TIME', line):
            self.currData['time'] = _findall('FROM\s+(\d+.\d+)\s+UNTIL\s+(\d+.\d+)', line)
        elif _match('^\s+FROM', line):
            self.currData['time'].append(_findall('FROM\s+(\d+.\d+)\s+UNTIL\s+(\d+.\d+)', line))
        elif _match('^\s+VEHICLE_CLASSES', line):
            self.currData['vehicle_classes'] = _findall('VEHICLE_CLASSES\s+(\d+)', line)[0]
            self.create(self.currData['link'], self.currData['at'], self.currData['vehicle_classes'], **self.currData)
        elif _match('^\s+PT', line):
            self.currData['PT'] = _findall('PT\s+(\d+)', line)[0]
            self.set(self.currData['number'], 'PT', self.currData['PT'])
        elif _match('^\s+ALTERNATIVES', line):
            self.set(self.currData['number'], 'alternatives', True)
        elif _match('^\s+ROUTE', line):
            self.over = False
            # Reset the variables from previous route
            self.currRouteNum = int(_findall('ROUTE\s+(\d+)', line)[0])
            self.destinationLink = _findall('LINK\s+(\d+)', line)[0]
            self.atLink = _findall('AT\s+(\d+.\d+)', line)[0]
        elif _match('^\s+FRACTION', line):
            currFraction = _findall('FRACTION\s+(\d+.\d+)', line)
            self.currRoute = self.Route(self.currRouteNum,
                                        self.destinationLink, self.atLink,
                                        currFraction)
            self.update(self.currData['number'], 'route', self.currRouteNum,
                        self.currRoute)
        elif _match('^\s+OVER', line):
            self.over = True
            self.currRoute.set('over', _findall('(\d+)',
                               line))
        elif self.over is True:
            self.currRoute.update('over', _findall('(\d+)', line))
        else:
            print 'Non-routing data provided: %s' % line

    def _output(self, routing):
        """ Outputs Route Decision syntax to VISSIM.
        """
        decNum = routing['number']
        vissimOut = []

        def _out(label, s=True):
            return self.get(decNum, label, string=s)
        vissimOut.append(str('ROUTING_DECISION ' + _out('number').ljust(4) +
                             ' NAME ' + _out('name') + ' LABEL ' +
                         _out('label', s=False)[0] + ' ' +
                         _out('label', s=False)[1]))
        vissimOut.append(str('LINK '.rjust(10) + _out('link') + 'AT '.rjust
                             (5) + _out('at')))
        timeStr = 'TIME'.rjust(9)
        for i in _out('time', s=False):
            timeStr += str('  FROM ' + str(i[0]) + ' UNTIL ' + str(i[1]))
        vissimOut.append(timeStr)
        if _out('vehicle_classes'):
            vissimOut.append('VEHICLE_CLASSES '.rjust(21) +
                             _out('vehicle_classes'))
        elif _out('PT'):
            vissimOut.append('PT '.rjust(21) + _out('PT'))
        for route in self.get(decNum, 'route', string=False).values():
            vissimOut += route.output()
        return vissimOut

    def export(self, filename):
        """ Prepare for export all routes in a given route object

            Input: Route object
            Output: List of all routes in VISSIM syntax
        """
        _exportSection(self, filename)


class Node:
    """ Handles Node section of .INP file.
    """
    def __init__(self, filename):
        self.filename = filename
        self.name = 'Nodes'
        self.data = {}
        self.curr_node_num = None
        self.curr_node = None
        self.node = None
        _importSection(self, filename)

    def _readSection(self, line):
        if line[0] == 'NODE':
            self.curr_node_num = int(line[1])
            self.data[self.curr_node_num] = {}
            self.curr_node = self.data[self.curr_node_num]
            self.curr_node['node'] = self.curr_node
            self.curr_node['name'] = line[3]
            self.curr_node['label'] = [line[5], line[6]]
        elif line[0] == 'EVALUATION':
            self.curr_node['evaluation'] = line[1]
        elif line[0] == 'NETWORK_AREA':
            self.curr_node['network_area'] = line[1]
            self.curr_node['over'] = []
            overs = int(line[1])
            for num in range(overs):
                self.curr_node['over'].append((line[(num*2)+2],
                                              line[(num*2)+3]))
        else:
            print 'Non-node data provided: %s' % line

    def _output(self, node):
        """ Outputs node syntax to VISSIM.

        Input: A single node dictionary
        Output: node back into VISSIM syntax
        """
        vissimOut = []
        vissimOut.append('NODE ' + str(node['node']) + ' NAME ' + node['name']
                          + ' LABEL ' + node['label'][0] + ' ' + node['label']
                          [1])
        vissimOut.append('EVALUATION '.rjust(13) + node['evaluation'])
        over_str = ''
        over_count = 0
        if 'over' in node:
            for i in node['over']:
                over_str += '  ' + str(i[0]) + ' ' + str(i[1])
                over_count += 1
            vissimOut.append('NETWORK_AREA '.rjust(15) + str(over_count) +
                              over_str)
        elif 'links' in node:
            for i in node['links']:
                over_str += '\nLINK '.rjust(10) + str(i).rjust(10)
            vissimOut.append('NETWORK_AREA'.rjust(16) + over_str)
        return vissimOut

    def export(self, filename):
        """ Prepare for export all node lots in a given node object

            Input: node object
            Output: List of all node lots in VISSIM syntax
        """
        _exportSection(self, filename)

    def createArea(self, area, **kwargs):
        if 'num' in kwargs:
            node_num = int(kwargs['num'])
        elif len(self.data.keys()) == 0:
            node_num = 1
        else:
            node_num = max(self.data.keys())+1
        self.data[node_num] = {}
        node = self.data[node_num]
        node['node'] = node_num
        node['over'] = area
        node['network_area'] = len(area)
        # Default values
        node['name'] = '""'
        node['label'] = ['0.00', '0.00']
        node['evaluation'] = 'NO'
        # User defined changes to the default values
        for name, value in kwargs.items():
            node[name] = value

    def createLink(self, link, **kwargs):
        if 'num' in kwargs:
            node_num = int(kwargs['num'])
        elif len(self.data.keys()) == 0:
            node_num = 1
        else:
            node_num = max(self.data.keys())+1
        self.data[node_num] = {}
        node = self.data[node_num]
        node['node'] = node_num
        node['links'] = link
        # Default values
        node['name'] = '""'
        node['label'] = ['0.00', '0.00']
        node['evaluation'] = 'NO'
        # User defined changes to the default values
        for name, value in kwargs.items():
            node[name] = value
