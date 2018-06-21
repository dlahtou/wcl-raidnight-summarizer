import pandas as pd
from os import listdir
from os.path import isfile, join
from raid_night_summarizer import Raidnight_Data
import datetime
import numpy as np
import re

ordered_handles = {"Garothi Worldbreaker": 1,
            "Felhounds of Sargeras": 2,
            "The Defense of Eonar": 3,
            "Portal Keeper Hasabel": 4,
            "Antoran High Command": 5,
            "Imonar the Soulhunter": 6,
            "Kin'garoth": 7,
            "Varimathras": 8,
            "The Coven of Shivarra": 9,
            "Aggramar": 10,
            "Argus the Unmaker": 11}

def raidmetaframe(raid_folder):
    '''
    Returns a dataframe for comparing all raidnights in a folder to each other
    '''
    # currently contains: raidnight best avg ilvl seen
    # TODO: Add columns for date, raid duration, bosses down

    raidmetadict = {'Date': [],
                    'Duration': [],
                    'Lockout Number': [],
                    'Average ilevel': []}

    boss_diffs_and_names = []
    for diffstring in ['Normal', 'Heroic', 'Mythic']:
        for bossname in ordered_handles.keys():
            boss_diffs_and_names.append(' '.join([diffstring, bossname]))
    
    for bossdn in boss_diffs_and_names:
        raidmetadict[bossdn] = []

    for filename in [f for f in listdir(raid_folder) if isfile(join(raid_folder, f))]:
        raidnight = Raidnight_Data(filename, raid_folder)

        raiddate = pd.to_datetime(datetime.date.fromtimestamp(raidnight.raidnight_date))
        raidmetadict['Date'].append(raiddate)

        raidnight_duration = pd.to_timedelta(datetime.datetime.fromtimestamp(raidnight.fights['end']//1000) - datetime.datetime.fromtimestamp(raidnight.fights['start']//1000))
        raidmetadict["Duration"].append(raidnight_duration)

        raidmetadict["Lockout Number"].append(raidnight.get_raid_lockout_period())

        top_average_ilevel = 0
        for boss in raidnight.damage_done.keys():
            try:
                player_ilevels = [x['itemLevel'] for x in raidnight.damage_done[boss]['entries']]
            except KeyError:
                continue
            average_ilevel = np.mean(player_ilevels)
            if average_ilevel > top_average_ilevel:
                top_average_ilevel = average_ilevel
        
        if top_average_ilevel != 0:
            raidmetadict["Average ilevel"].append(top_average_ilevel)
        else:
            raidmetadict["Average ilevel"].append(None)
        
        for boss in boss_diffs_and_names:
            if boss in raidnight.damage_done.keys():
                raidmetadict[boss] = True
            else:
                raidmetadict[boss] = None

    raidmetaframe = pd.DataFrame.from_dict(raidmetadict)
    print(raidmetaframe.head(1))

raidmetaframe('MyDudes')