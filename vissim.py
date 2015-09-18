#!/usr/bin/env python
""" VISSIM Tools v.0. """
from re import findall as _findall
from math import sqrt as _sqrt
import regex

def _median(lst):
    """ Stock median function from: http://stackoverflow.
    com/questions/24101524/finding-median-of-list-in-python
    """
    lst = sorted(lst)
    if len(lst) < 1:
        return None
    if len(lst) % 2 == 1:
        return lst[((len(lst)+1)/2)-1]
    else:
        return float(sum(lst[(len(lst)/2)-1:(len(lst)/2)+1]))/2.0


def _removeQuotes(line):
    """ Process VISSIM text such that double quotations don't get split by
    space delimiter.
    """
    if '"' in line:
        matches = _findall(r'\"(.+?)\"', line)
        matchblank = _findall(r'\"(.?)\"', line)
        final_line = []
        line = line.split('"')
        for i in line:
            if i in matches:
                final_line.append('"' + i + '"')
                matches.remove(i)
            elif i in matchblank:
                final_line.append('""')
                matchblank.remove(i)
            else:
                final_line += i.split()
        return final_line
    else:
        return line.strip().split()


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
                elif len(found) > 0:
                    section = found[0]
                elif section == name and row[0] is not '-':
                    obj._readSection(_removeQuotes(row))
                else:
                    continue
    except IOError:
        print 'cannot open', filename


def _updateFile(org_file, new_file, name, print_data):
    """ Update a section of a VISSIM .INP file.
        Inputs: filename, object type(Inputs, Routing Decision, etc.) and list
        of strings with VISSIM syntax.
        Outputs: new file
    """
    search = '-- ' + name + ': --'
    f = open(org_file, 'r')
    lines = f.readlines()
    f.close()
    f = open(new_file, 'w')
    start_delete = False
    print 'Writing %s to %s ...' % (name, new_file)
    for line in lines:
        if start_delete is True and line[:3] == '-- ':
            start_delete = False
            f.write(line)
        if line[:len(search)] == search:
            start_delete = True
            for new_line in print_data:
                f.write(str(new_line) + '\n')
        if start_delete is False:
            f.write(line)
    f.close()


def _exportSection(obj, filename):
    """ Prepare for export all dictionaries within a given object

        Input: Dict object
        Output: List of all items for a given class in VISSIM syntax
    """
    first_line = '-- ' + obj.name + '--\n'
    second_line = '-' * len(first_line) + '\n'
    print_data = [first_line + second_line]
    print 'Reading %s ...' % obj.name
    for value in obj.data.values():
        print_data += obj.output(value)
    print 'Updating %s ...' % obj.name
    _updateFile(obj.filename, filename, obj.name, print_data)


def _getLineVariable(match, line, items=1, multi=False):
    """ Matches the text string corresponding to a VISSIM parameter and
    returns its value. If mult is True, return a list, otherwise return a
    string.
    """
    if items > 1:
        w = '\w+' + (' \w+' * (items - 1))
    else:
        w = 'w\+'
    re_string = '(?<=%s\s{1,})%s' % (match, w)
    if multi:
        m = regex.findall(re_string, line)
        return m
    else:
        if items > 1:
            m = regex.findall(re_string, line)
            return m[0].split(' ')
        else:
            m = regex.findall(re_string, line)
            return m


def _checkStr(data, key):
    """ Checks if key is a str, if not converts and checks its existence
    """
    if isinstance(key, str) is False:
        key = str(key)
    key = key.lower()
    if key not in data:
        raise KeyError('%s not in data' % (key))
    return key


def _getData(data, key, label):
    """ Returns requested value from vissim object
    """
    key = _checkStr(data, key)
    label = _checkStr(data[key], label)
    value = data[key][label]
    return value


def _setData(data, key, label, value):
    """ Sets given value in vissim object
    """
    key = _checkStr(data, key)
    label = _checkStr(data[key], label)
    data[key][label] = value


def _clearAll(data, label):
    """ Clears values for a given label in visism object.
    """
    for key in data.keys():
        label = _checkStr(data[key], label)
        _setData(data, key, label, '')


class Inputs:
    """ Handles Inputs section of .INP file.
    """
    def __init__(self, filename):
        self.filename = filename
        self.name = 'Inputs'
        self.data = {}
        self.curr_data = None
        _importSection(self, filename)

    def _readSection(self, line):
        """ Process the Input section of the INP file.
        """
        if line[0] == 'INPUT':
            self.data[line[1]] = {'input': line[1]}
            self.curr_data = self.data[line[1]]
        elif line[0] == 'NAME':
            self.curr_data['name'] = line[1]
            self.curr_data['label'] = line[3]
        elif line[0] == 'LINK':
            self.curr_data['link'] = line[1]
            if line[3] == 'EXACT':
                self.curr_data['exact'] = True
                i = 1
            else:
                i = 0
                self.curr_data['exact'] = False
            self.curr_data['Q'] = line[3+i]
            curr_comp = line[5+i]
            self.curr_data['composition'] = curr_comp
        elif line[0] == 'TIME':
            self.curr_data['from'] = line[2]
            self.curr_data['until'] = line[4]
        else:
            print 'Non-input data provided: %s' % line

    def __output(self, inputs):
        """ Outputs Inputs syntax to VISSIM.

        Input: A single Inputs dictionary
        Output: Inputs back into VISSIM syntax
        """
        vissim_out = []
        vissim_out.append('INPUT ' + str(inputs['input']).rjust(6))
        vissim_out.append('NAME '.rjust(10) + inputs['name'] + ' LABEL  ' +
                          inputs['label'][0] + ' ' + inputs['label'][1])
        if inputs['exact'] is True:
            vissim_out.append('LINK '.rjust(10) + inputs['link'] + ' Q EXACT '
                              + str(int(float(inputs['Q']))) + '.000 \
                              COMPOSITION ' + str(inputs['composition']))
        else:
            vissim_out.append('LINK '.rjust(10) + inputs['link'] + ' Q ' + str(
                             int(float(inputs['Q']))) + '.000 COMPOSITION ' +
                             str(inputs['composition']))
        vissim_out.append('TIME FROM '.rjust(15) + inputs['from'] + ' UNTIL ' +
                          inputs['until'])
        return vissim_out

    def __export(self, filename):
        """ Prepare for export all inputs in a given inputs object

            Input: Inputs object
            Output: List of all inputs in VISSIM syntax
        """
        _exportSection(self, filename)

    def updateInput(self, link, time_from, time_until, composition, demand):
        """ Update demand values for a given link, time period and composition
        """
        compare_dict = {'link': link, 'from': time_from, 'until': time_until,
                        'composition': composition}
        for inp in self.data.values():
            if {key: inp[key] for key in compare_dict.keys()} == compare_dict:
                inp['Q'] = demand

    def create(self, link, demand, composition, **kwargs):
        inputs_num = str(kwargs.get('inputs', max(self.data.keys())+1))
        self.data[inputs_num] = {}
        self.curr_data = self.data[inputs_num]
        self.curr_data['inputs'] = inputs_num
        self.curr_data['Q'] = demand
        self.curr_data['link'] = link
        self.curr_data['composition'] = composition
        # Default values
        self.curr_data['name'] = kwargs.get('name', '""')
        self.curr_data['label'] = kwargs.get('label', ['0.00', '0.00'])
        self.curr_data['from'] = kwargs.get('from', [0.000])
        self.curr_data['until'] = kwargs.get('until', [3600.00])
        assert len(self.data['from']) == len(self.data['to']) == len(self.data[
               'Q']) == len(self.data['composition'])

    def get(self, inputnum, label):
        """ Get value from Input.
            Input: Input number, Value label
            Output: Value
        """
        return _getData(self.data, inputnum, label)

    def set(self, inputnum, label, value):
        """ Set value from Input.
            Input: Input number, Value label, value
            Output: Change is made in place
        """
        _setData(self.data, inputnum, label, value)

    def getInputNumByLink(self, linknum):
        """ Get value from Input by link number
            Input: Link number
            Output: Input number as key, time and composition as values
        """
        if isinstance(linknum, str) is False:
            linknum = str(linknum)
        result = {k: {'from': v['from'], 'until': v['until'], 'composition':
                      v['composition']} for k, v in self.data.items()
                  if v['link'] == linknum}
        if len(result) == 0:
            raise KeyError('%s not in data' % (linknum))
        else:
            return result


class Links:
    """ Handles Links section of .INP file.
    """
    def __init__(self, filename):
        self.filename = filename
        self.name = 'Links'
        self.data = {}
        self.over = None
        self.curr_data = None
        self.closed = None
        _importSection(self, filename)

    def _readSection(self, line):
        if line[0] == 'LINK':
            # Link number is dictionary key
            self.data[line[1]] = {}
            self.curr_data = self.data[line[1]]
            self.curr_data['link'] = line[1]
            self.curr_data['name'] = line[3]
            self.curr_data['label'] = [line[5], line[6]]
            self.over = False
        elif line[0] == 'BEHAVIORTYPE':
            self.curr_data['behaviortype'] = line[1]
            self.curr_data['displaytype'] = line[3]
        elif line[0] == 'LENGTH':
            self.curr_data['length'] = line[1]
            self.curr_data['lanes'] = line[3]
            self.curr_data['lane_width'] = []
            count = 4
            if int(line[3]) > 1:
                for i in range(int(line[3])):
                    self.curr_data['lane_width'].append(line[5+i])
                    count += 1
            else:
                self.curr_data['lane_width'] = [line[5]]
                count += 1
            self.curr_data['gradient'] = line[count+2]
            self.curr_data['cost'] = line[count+4]
            self.curr_data['surcharge1'] = line[count+6]
            self.curr_data['segment_length'] = line[count+11]
            if line[-1] == 'EVALUATION':
                self.curr_data['evaluation'] = ' EVALUATION'
            else:
                self.curr_data['evaluation'] = ''
        elif line[0] == 'FROM':
            self.curr_data['from'] = (float(line[1]), float(line[2]))
        elif line[0] == 'OVER' and self.over is False:
            self.curr_data['over'] = []
            size = int(len(line)/float(4))
            for coord in range(size):
                x = float(line[(4*coord)+1])
                y = float(line[(4*coord)+2])
                self.curr_data['over'].append((x, y))
            self.over = True
        elif line[0] == 'OVER' and self.over is True:
            size = int(len(line)/float(4))
            for coord in range(size):
                x = float(line[(4*coord)+1])
                y = float(line[(4*coord)+2])
                self.curr_data['over'].append((x, y))
        elif line[0] == 'TO':
            self.curr_data['to'] = (float(line[1]), float(line[2]))
        elif line[0] == 'CLOSED':
            self.curr_data['closed'] = {}
        elif 'closed' in self.curr_data and line[0] == 'LANE':
            lane = line[1]
            veh_classes = line[3:]
            self.curr_data['closed'][lane] = veh_classes
        else:
            print 'Non-link data provided: %s' % line

    def __output(self, links):
        """ Outputs Links syntax to VISSIM.

        Input: A single links dictionary
        Output: Route decisions back into VISSIM syntax
        """
        vissim_out = []
        vissim_out.append('LINK ' + str(links['link']).rjust(6) + ' NAME ' +
                          links['name'] + ' LABEL ' + links['label'][0] + ' ' +
                          links['label'][1])
        vissim_out.append('BEHAVIORTYPE '.rjust(15) + links['behaviortype'].
                          rjust(5) + ' DISPLAYTYPE' + links['displaytype'].
                          rjust(5))
        lane_width_str = ''
        if len(links['lane_width']) > 1:
            for width in links['lane_width']:
                lane_width_str += width.rjust(5)
        else:
            lane_width_str = links['lane_width'][0].rjust(5)
        vissim_out.append('LENGTH '.rjust(9) + str(links['length']).rjust(8) +
                          ' LANES ' + links['lanes'].rjust(2) + ' LANE_WIDTH '
                          + lane_width_str + ' GRADIENT ' + links['gradient'].
                          ljust(10) + ' COST ' + links['cost'].ljust(7) +
                          ' SURCHARGE ' + links['surcharge1'] + ' SURCHARGE ' +
                          links['surcharge1'] + ' SEGMENT LENGTH ' + links[
                          'segment_length'].rjust(8) + links['evaluation'])
        vissim_out.append('FROM '.rjust(7) + str(links['from'][0]) + ' ' + str(
                          links['from'][1]))
        if 'over' in links:
            over_str = ' '
            for i in links['over']:
                over_str += ' OVER ' + str(i[0]) + ' ' + str(i[1]) + ' 0.000'
            vissim_out.append(over_str)
        vissim_out.append('TO '.rjust(5) + str(links['to'][0]).rjust(10) + ' '
                          + str(links['to'][1]))
        return vissim_out

    def __export(self, filename):
        """ Prepare for export all links in a given links object

            Input: Links object
            Output: List of all links in VISSIM syntax
        """
        _exportSection(self, filename)

    def createLink(self, coord_from, coord_to, **kwargs):
        link_num = kwargs.get('link', max(self.data.keys())+1)
        self.data[link_num] = {}
        link = self.data[link_num]
        link['link'] = link_num
        link['from'] = coord_from
        link['to'] = coord_to
        # Default values
        link['name'] = kwargs.get('name', '""')
        link['behaviortype'] = kwargs.get('behaviortype', '1')
        link['cost'] = kwargs.get('cost', '0.00000')
        link['displaytype'] = kwargs.get('displaytype', '1')
        link['gradient'] = kwargs.get('gradient', '0.00000')
        link['label'] = kwargs.get('label', ['0.00', '0.00'])
        link['lane_width'] = kwargs.get('lane_width', ['3.66'])
        link['lanes'] = kwargs.get('lanes', '1')
        link['segment_length'] = kwargs.get('segment_length', '10.000')
        link['surcharge1'] = kwargs.get('surcharge1', '0.00000')
        link['evaluation'] = kwargs.get('evaulation', '""')
        link['over'] = kwargs.get('over', None)
        if link['over']:
            link['length'] = 0
            x1, y1 = link['from']
            for coord in link['over']:
                x2, y2 = coord
                dx, dy = x2-x1, y2-y1
                link['length'] += _sqrt(dx**2 + dy**2)
                x1, y1 = x2, y2
            link['length'] = str(round(link['length'], 3))
        else:
            link['length'] = str(round(_sqrt((link['to'][0]-link['from'][0])**2
                                 + (link['to'][1]-link['from'][1])**2), 3))


class Connector:
    """ Handles Connector section of .INP file.
    """
    def __init__(self, filename):
        self.filename = filename
        self.name = 'Connectors'
        self.data = {}
        self.curr_data = None
        self.curr_lane = None
        _importSection(self, filename)

    def _readSection(self, line):
        if line[0] == 'CONNECTOR':
            # Connector number is dictionary key
            self.data[line[1]] = {}
            self.curr_data = self.data[line[1]]
            self.curr_data['connector'] = line[1]
            self.curr_data['name'] = line[3]
            self.curr_data['label'] = [line[5], line[6]]
        elif line[0] == 'FROM':
            if len(line) == 7:
                self.curr_data['from'] = line[2]
                self.curr_data['from_lanes'] = [line[4]]
                self.curr_data['from_at'] = line[6]
            else:
                lane_num = len(line) - 7
                self.curr_data['from'] = line[2]
                self.curr_data['from_lanes'] = [line[4]]
                for lanes in range(1, lane_num+1):
                    self.curr_data['from_lanes'].append(line[4+lanes])
                self.curr_data['from_at'] = line[6+lane_num]
        elif line[0] == 'OVER':
            self.curr_data['over'] = self.curr_data.get('over', [])
            overs = len(line)/4
            for num in range(overs):
                self.curr_data['over'].append((line[(num*4)+1],
                                              line[(num*4)+2]))
        elif line[0] == 'TO':
            if len(line) == 12:
                self.curr_data['to'] = line[2]
                self.curr_data['to_lanes'] = [line[4]]
                self.curr_data['to_at'] = line[6]
                self.curr_data['behaviortype'] = line[8]
                self.curr_data['displaytype'] = line[10]
            else:
                lane_num = len(line) - 12
                self.curr_data['to'] = line[2]
                self.curr_data['to_lanes'] = [line[4]]
                for lanes in range(1, lane_num+1):
                    self.curr_data['to_lanes'].append(line[4+lanes])
                self.curr_data['to_at'] = line[6+lane_num]
                self.curr_data['behaviortype'] = line[8+lane_num]
                self.curr_data['displaytype'] = line[10+lane_num]
        elif line[0] == 'DX_EMERG_STOP':
            self.curr_data['dx_emerg_stop'] = line[1]
            self.curr_data['dx_lane_change'] = line[3]
        elif line[0] == 'GRADIENT':
            self.curr_data['gradient'] = line[1]
            self.curr_data['cost'] = line[3]
            self.curr_data['surcharge1'] = line[5]
            self.curr_data['surcharge2'] = line[7]
        elif line[0] == 'SEGMENT':
            self.curr_data['segment_length'] = line[2]
            if line[3] == 'NONE':
                self.curr_data['visualization'] = False
            else:
                self.curr_data['visualization'] = True
        elif line[0] == 'NOLANECHANGE':
            self.curr_data['nolanechange'] = {}
            for i, j in enumerate(line):
                if j == 'LANE':
                    self.curr_data['nolanechange'][line[i+1]] = {}
                    self.curr_lane = self.curr_data['nolanechange'][line[i+1]]
                elif j == 'LEFT':
                    self.curr_lane['left'] = [v for v in
                                              line[i+1:None if 'LANE' or
                                                   'RIGHT' not in line[i+1:]
                                                   else min([line[i+1:].index
                                                            ('LANE'), line
                                                            [i+1:].index
                                                            ('RIGHT')])]]
                elif j == 'RIGHT':
                    self.curr_lane['right'] = [v for v in
                                               line[i+1:None if 'LANE' or
                                                    'LEFT' not in line[i+1:]
                                                    else min([line[i+1:].
                                                              index('LANE'),
                                                              line[i+1:].index
                                                              ('LEFT')])]]
        else:
            print 'Non-connector data provided: %s' % line

    def __output(self, connector):
        """ Outputs connector syntax to VISSIM.

        Input: A single connector dictionary
        Output: connector back into VISSIM syntax
        """
        vissim_out = []
        vissim_out.append('CONNECTOR ' + str(connector['connector']) + ' NAME '
                          + connector['name'] + ' LABEL ' + connector['label']
                          [0] + ' ' + connector['label'][1])
        from_lanes_str = ''
        for i in connector['from_lanes']:
            from_lanes_str += i + ' '
        vissim_out.append('FROM LINK '.rjust(12) + str(connector['from']) +
                          ' LANES ' + from_lanes_str + 'AT ' + connector
                          ['from_at'])
        over_str = ''
        for i in connector['over']:
            over_str += 'OVER ' + str(i[0]) + ' ' + str(i[1]) + ' 0.000 '
        vissim_out.append('  ' + over_str)
        to_lanes_str = ''
        for i in connector['to_lanes']:
            to_lanes_str += i + ' '
        vissim_out.append('TO LINK '.rjust(10) + str(connector['to']) +
                          ' LANES '.rjust(7) + to_lanes_str + 'AT ' + connector
                          ['to_at'].ljust(6) + ' BEHAVIORTYPE ' + connector
                          ['behaviortype'] + ' DISPLAYTYPE ' + connector
                          ['displaytype'] + ' ALL')
        vissim_out.append('DX_EMERG_STOP '.rjust(16) + connector
                          ['dx_emerg_stop'] + ' DX_LANE_CHANGE ' + connector
                          ['dx_lane_change'])
        vissim_out.append('GRADIENT '.rjust(11) + connector['gradient'] +
                          ' COST ' + connector['cost'] + ' SURCHARGE ' +
                          connector['surcharge1'] + ' SURCHARGE ' + connector
                          ['surcharge2'])
        if connector['visualization'] == False:
            vissim_out.append('SEGMENT LENGTH '.rjust(17) + connector
                              ['segment_length'] + ' NONE ANIMATION')
        else:
            vissim_out.append('SEGMENT LENGTH '.rjust(17) + connector
                              ['segment_length'] + ' ANIMATION')
        return vissim_out

    def __export(self, filename):
        """ Prepare for export all connector lots in a given connector object

            Input: connector object
            Output: List of all connector lots in VISSIM syntax
        """
        _exportSection(self, filename)

    def create(self, from_link, to_link, **kwargs):
        connector_num = str(kwargs.get('num', max(self.data.keys() or [0])+1))
        self.data[connector_num] = {}
        connector = self.data[connector_num]
        connector['connector'] = connector_num
        connector['from'] = from_link
        connector['to'] = to_link
        # Default values
        connector['label'] = kwargs.get('label', ['0.00', '0.00'])
        connector['from_lanes'] = kwargs.get('from_lanes', '1')
        connector['from_at'] = kwargs.get('from_at', self.data[from_link]
                                          ['length'])
        # Calculate default spline points between from link and to link:
        over1 = self.data[from_link]['to']
        over4 = self.data[to_link]['from']
        if over4[0] == over1[0] and over4[1] == over1[1]:
            over1 = (self.data[from_link]['to'][0], self.data[from_link]['to']
                     [1]+0.001)
            over2 = (over4[0]+0.001, over4[1])
            over3 = (_median([over2[0], over4[0]]), _median([over2[1],
                     over4[1]]))
        else:
            over2 = (_median([over4[0], over1[0]]), _median([over4[1],
                     over1[1]]))
            over3 = (_median([over2[0], over4[0]]), _median([over2[1],
                     over4[1]]))
        connector['over'] = kwargs.get('over', [over1, over2, over3, over4])
        connector['name'] = kwargs.get('name', '""')
        connector['to_lanes'] = kwargs.get('to_lanes', '1')
        connector['to_at'] = kwargs.get('to_at', '0.000')
        connector['behaviortype'] = kwargs.get('behaviortype', '1')
        connector['displaytype'] = kwargs.get('displaytype', '1')
        connector['dx_emerg_stop'] = kwargs.get('dx_emerg_stop', '4.999')
        connector['dx_lane_change'] = kwargs.get('dx_lane_change', '200.010')
        connector['gradient'] = kwargs.get('gradient', '0.00000')
        connector['cost'] = kwargs.get('cost', '0.00000')
        connector['surcharge1'] = kwargs.get('surcharge1', '0.00000')
        connector['surcharge2'] = kwargs.get('surcharge2', '0.00000')
        connector['segment_length'] = kwargs.get('segment_length', '10.000')
        connector['visualization'] = kwargs.get('visualization', True)


class Parking:
    """ Handles Parking section of .INP file.
    """
    def __init__(self, filename):
        self.filename = filename
        self.name = 'Parking Lots'
        self.data = {}
        self.curr_data = None
        _importSection(self, filename)

    def _readSection(self, line):
        if line[0] == 'PARKING_LOT':
            # Parking lot number is dict key
            self.data[line[1]] = {}
            self.curr_data = self.data[line[1]]
            self.curr_data['parking'] = line[1]
            self.curr_data['name'] = line[3]
            self.curr_data['label'] = [line[5], line[6]]
        elif line[0] == 'PARKING_SPACES':
            self.curr_data['spaces_length'] = line[2]
        elif line[0] == 'ZONES':
            self.curr_data['zones'] = line[1]
            self.curr_data['fraction'] = line[3]
        elif line[0] == 'POSITION':
            self.curr_data['position_link'] = line[2]
            if len(line) == 7:
                self.curr_data['lane'] = line[4]
                self.curr_data['at'] = line[6]
            elif len(line) == 5:
                self.curr_data['at'] = line[4]
        elif line[0] == 'LENGTH':
            self.curr_data['length'] = line[1]
        elif line[0] == 'CAPACITY':
            self.curr_data['capacity'] = line[1]
        elif line[0] == 'OCCUPANCY':
            self.curr_data['occupancy'] = line[1]
        elif line[0] == 'DEFAULT':
            self.curr_data['desired_speed'] = line[2]
        elif line[0] == 'OPEN_HOURS':
            self.curr_data['open_hours'] = (line[2], line[4])
        elif line[0] == 'MAX_TIME':
            self.curr_data['max_time'] = line[1]
        elif line[0] == 'FLAT_FEE':
            self.curr_data['flat_fee'] = line[1]
        elif line[0] == 'FEE_PER_HOUR':
            self.curr_data['fee_per_hour'] = line[1]
        elif line[0] == 'ATTRACTION':
            self.curr_data['attraction'] = line[1]
        elif line[0] == 'COMPOSITION':
            self.curr_data['composition'] = line[1]
        else:
            print 'Non-parking data provided: %s' % line

    def __output(self, parking):
        """ Outputs Parking syntax to VISSIM.

        Input: A single parking dictionary
        Output: Parking back into VISSIM syntax
        """
        vissim_out = []
        vissim_out.append('PARKING_LOT ' + str(parking['parking']) + ' NAME ' +
                          parking['name'] + ' LABEL ' + parking['label'][0] +
                          ' ' + parking['label'][1])
        if 'spaces_length' in parking:
            vissim_out.append('PARKING_SPACES LENGTH '.rjust(24) + parking
                              ['spaces_length'])
        vissim_out.append('ZONES '.rjust(8) + parking['zones'].rjust(6) +
                          ' FRACTION ' + parking['fraction'].rjust(7))
        if 'lane' in parking:
            vissim_out.append('POSITION LINK '.rjust(16) + str(parking[
                              'position_link']) + ' LANE ' + str(parking
                              ['lane']) + ' AT ' + str(parking['at']))
        else:
            vissim_out.append('POSITION LINK '.rjust(16) + str(parking
                              ['position_link']) + ' AT ' + str(parking['at']))
        vissim_out.append('LENGTH '.rjust(9) + str(parking['length']).rjust(9))
        vissim_out.append('CAPACITY   '.rjust(13) + parking['capacity'])
        vissim_out.append('OCCUPANCY '.rjust(12) + parking['occupancy'])
        vissim_out.append('DEFAULT DESIRED_SPEED '.rjust(24) + parking
                          ['desired_speed'])
        vissim_out.append('OPEN_HOURS  FROM '.rjust(19) + parking['open_hours']
                          [0].ljust(2) + ' UNTIL ' + parking['open_hours'][1])
        vissim_out.append('MAX_TIME '.rjust(11) + parking['max_time'])
        vissim_out.append('FLAT_FEE '.rjust(11) + parking['flat_fee'])
        vissim_out.append('FEE_PER_HOUR '.rjust(15) + parking['fee_per_hour'])
        vissim_out.append('ATTRACTION '.rjust(13) + parking['attraction'])
        if 'composition' in parking:
            vissim_out.append('COMPOSITION '.rjust(14) + parking
                              ['composition'])
        return vissim_out

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
        self.curr_data = None
        _importSection(self, filename)

    def _readSection(self, line):
        """ Process the Transit Decision section of the INP file
        """
        if line[0] == "LINE":
            # Dictionary key is the line number
            self.data[line[1]] = {}
            self.curr_data = self.data[line[1]]
            self.curr_data['line'] = line[1]
            self.curr_data['name'] = line[3]
            self.curr_data['route'] = line[7]
            self.curr_data['priority'] = line[9]
            self.curr_data['length'] = line[11]
            self.curr_data['mdn'] = line[13]
            if len(line) == 14:
                self.curr_data['pt'] = True
        elif line[0] == "ANM_ID":
            self.curr_data['link'] = line[4]
            self.curr_data['desired_speed'] = line[6]
            self.curr_data['vehicle_type'] = line[8]
        elif line[0] == "COLOR":
            self.curr_data['color'] = line[1]
            self.curr_data['time_offset'] = line[3]
        elif line[0] == "DESTINATION":
            self.curr_data['destination_link'] = line[2]
            self.curr_data['at'] = line[4]
        elif line[0] == "START_TIMES":
            self.curr_data['start_times'] = []
            num = (len(line)-1)/5
            for i in range(num):
                self.curr_data['start_times'].append([line[1+(5*i)], line
                                                     [3+(5*i)], line[5+(5*i)]])
        elif line[1] == "COURSE":
            num = (len(line)/5)
            for i in range(num):
                self.curr_data['start_times'].append([line[(5*i)], line
                                                     [2+(5*i)], line[4+(5*i)]])
        else:
            print 'Non-transit data provided: %s' % line

    def __output(self, transit):
        """ Outputs transit Decision syntax to VISSIM.

        Input: A single transit decision dictionary
        Output: transit decisions back into VISSIM syntax
        """
        vissim_out = []
        pt = ''
        if transit['pt'] == True:
            pt = ' PT_TELE'
        vissim_out.append(str('LINE ' + transit['line'].rjust(4) + ' NAME ' +
                              transit['name'] + '  LINE ' + transit['line'].
                              rjust(3) + '  ROUTE ' + transit['route'].rjust(3)
                              + '    PRIORITY ' + transit['priority'] +
                              '  LENGTH ' + transit['length'] + '  MDN ' +
                              transit['mdn']) + pt + '\n')
        vissim_out.append(str('ANM_ID '.rjust(12) + transit['anm'] +
                              ' SOURCE    LINK ' + transit['link'] +
                              ' DESIRED_SPEED ' + transit['desired_speed'] +
                              ' VEHICLE_TYPE ' + transit['vehicle_type']))
        vissim_out.append(str('COLOR '.rjust(24) + transit['color'] +
                              ' TIME_OFFSET ' + transit['time_offset'].
                              rjust(6)))
        vissim_out.append(str('DESTINATION    LINK '.rjust(32) + transit
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
            vissim_out.append(time_str)
        return vissim_out

    def __export(self, filename):
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
        self.curr_data = None
        self.time_periods = None
        self.destination_link = None
        self.at_link = None
        self.curr_route_num = None
        self.curr_route = None
        self.over = None
        _importSection(self, filename)

    class Route:
        """ Individual routes within a given Route Decisions
        """
        def __init__(self, route_num, destination_link, at_link, fraction):
            self.name = 'Route'
            self.data = {'number': route_num, 'link': destination_link,
                         'at': at_link, 'fraction': fraction}

        def __output(self):
            """ Outputs Route syntax to VISSIM.
            """
            route = self.data
            vissim_out = []
            vissim_out.append('ROUTE '.rjust(11) + route['number'].rjust(6) +
                              ' DESTINATION LINK' + route['link'].rjust(6) +
                              ' AT' + route['at'].rjust(9))
            fraction_str = ''
            for j in route['fraction']:
                fraction_str += 'FRACTION '.rjust(16) + j
            vissim_out.append(fraction_str)
            # Sometimes the route ends on the same link it began:
            if 'over' in route:
                return vissim_out
            else:
                for count, j in enumerate(route['over']):
                    if count == 0:
                        over_str = 'OVER '.rjust(11)
                        over_str += j.rjust(6)
                    elif count == len(route['over']) - 1:
                        over_str += j.rjust(6)
                        vissim_out.append(over_str)
                        break
                    elif (count + 1 % 10) == 0:
                        over_str += j.rjust(6)
                        vissim_out.append(over_str)
                        over_str = ' '*11
                    else:
                        over_str += j.rjust(6)
                    if len(route['over']) == 1:
                        vissim_out.append(over_str)
                return vissim_out

        def get(self, routenum, label):
            """ Get value from Route.
                Input: Route number, Value label
                Output: Value
            """
            return _getData(self.data, routenum, label)

        def set(self, routenum, label, value):
            """ Set value from Route.
                Input: Route number, Value label, value
                Output: Change is made in place
            """
            _setData(self.data, routenum, label, value)

    def _readSection(self, line):
        """ Process the Route Decision section of the INP file
        """
        if line[0] == "ROUTING_DECISION":
            # Reset from previous routes
            self.curr_route = None
            self.over = False
            # Routing decision number is dict key
            self.data[line[1]] = {'route': {}}
            self.curr_data = self.data[line[1]]
            self.curr_data['number'] = line[1]
            self.curr_data['name'] = line[3]
            self.curr_data['label'] = [line[5], line[6]]
        elif line[0] == "LINK":
            self.curr_data['link'] = line[1]
            self.curr_data['at'] = line[3]
        elif line[0] == "TIME":
            self.time_periods = (len(line)-1)/4
            self.curr_data['time'] = []
            for i in range(self.time_periods):
                start = line[2+(4*i)]
                end = line[4+(4*i)]
                self.curr_data['time'].append((start, end))
        elif line[0] == "VEHICLE_CLASSES":
            self.curr_data['vehicle_classes'] = line[1]
        elif line[0] == "PT":
            self.curr_data['PT'] = line[1]
        elif line[0] == "ALTERNATIVES":
            self.curr_data['alternatives'] = True
        elif line[0] == "ROUTE":
            # Reset the variables from previous route
            self.over = False
            self.curr_route_num = line[1]
            self.destination_link = line[4]
            self.at_link = line[6]
        elif line[0] == "FRACTION":
            curr_fraction = []
            for i in range(self.time_periods):
                fraction = line[1+(i*2)]
                curr_fraction.append(fraction)
            self.curr_route = self.Route(self.curr_route_num,
                                         self.destination_link, self.at_link,
                                         curr_fraction)
            self.curr_data['route'][self.curr_route_num] = self.curr_route
        elif line[0] == "OVER":
            self.over = True
            self.curr_route.data['over'] = line[1:]
        elif self.over is True:
            self.curr_route.data['over'] += line
        else:
            print 'Non-routing data provided: %s' % line

    def __output(self, routing):
        """ Outputs Route Decision syntax to VISSIM.
        """
        vissim_out = []
        vissim_out.append(str('ROUTING_DECISION ' + routing['number'].ljust(4)
                              + ' NAME ' + routing['name'] + ' LABEL ' +
                              routing['label'][0] + ' ' + routing['label'][1]))
        vissim_out.append(str('LINK '.rjust(10) + routing['link'] + 'AT '.rjust
                              (5) + routing['at']))
        time_str = 'TIME'.rjust(9)
        for i in routing['time']:
            time_str += str('  FROM ' + i[0] + ' UNTIL ' + i[1])
        vissim_out.append(time_str)
        if 'vehicle_classes' in routing:
            vissim_out.append('VEHICLE_CLASSES '.rjust(21) + routing
                              ['vehicle_classes'])
        elif 'PT' in routing:
            vissim_out.append('PT '.rjust(21) + routing['PT'])
        for route in routing['route'].values():
            vissim_out += route.output()
        return vissim_out

    def __export(self, filename):
        """ Prepare for export all routes in a given route object

            Input: Route object
            Output: List of all routes in VISSIM syntax
        """
        _exportSection(self, filename)

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

    def get(self, decnum, label):
        """ Get value from Routing data.
            Input: Routing decision number, Value label
            Output: Value
        """
        return _getData(self.data, decnum, label)

    def set(self, decnum, label, value):
        """ Set value from Routing data.
            Input: Routing decision number, Value label, value
            Output: Change is made in place
        """
        _setData(self.data, decnum, label, value)

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

    def __output(self, node):
        """ Outputs node syntax to VISSIM.

        Input: A single node dictionary
        Output: node back into VISSIM syntax
        """
        vissim_out = []
        vissim_out.append('NODE ' + str(node['node']) + ' NAME ' + node['name']
                          + ' LABEL ' + node['label'][0] + ' ' + node['label']
                          [1])
        vissim_out.append('EVALUATION '.rjust(13) + node['evaluation'])
        over_str = ''
        over_count = 0
        if 'over' in node:
            for i in node['over']:
                over_str += '  ' + str(i[0]) + ' ' + str(i[1])
                over_count += 1
            vissim_out.append('NETWORK_AREA '.rjust(15) + str(over_count) +
                              over_str)
        elif 'links' in node:
            for i in node['links']:
                over_str += '\nLINK '.rjust(10) + str(i).rjust(10)
            vissim_out.append('NETWORK_AREA'.rjust(16) + over_str)
        return vissim_out

    def __export(self, filename):
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
