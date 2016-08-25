import gspread
import vissim_v8 as vissim
from oauth2client.service_account import ServiceAccountCredentials
import numpy as np

scope = ['https://spreadsheets.google.com/feeds']
credentials = (ServiceAccountCredentials.from_json_keyfile_name(
               '/Users/brian/.ssh//GoogleOAuth.json', scope))

gc = gspread.authorize(credentials)
wks = gc.open('Temescal Model').sheet1
inputRange = 'T2:V6'
volRange = 'T9:X15'

inputs = np.array(wks.range(inputRange)).reshape((5, 3))
vols = np.array(wks.range(volRange)).reshape((7, 5))

inputsDict = {i[0].value: i[2].value for i in inputs}
volsDict = {i[0].value: {i[1].value[-2:] + 'L': i[2].value, i[1].value[-2:] +
                         'T': i[3].value, i[1].value[-2:] + 'R': i[4].value}
            for i in vols}

v = vissim.Vissim('test_networks/temescal.inpx')

# Update inputs
for no, demand in inputsDict.items():
    index = 0
    v.inputs.updateVol(no, index, demand)

# Update turn vols
for routingNum, turns in volsDict.items():
    for turn, vol in turns.items():
        if vol == '':
            continue
        else:
            routeNum = v.routing.getRoute(routingNum, 'name', turn)['no']
            v.routing.updateFlow(routingNum, routeNum, vol)
