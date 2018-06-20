from raid_night_summarizer import *
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from textwrap import wrap
import re
import pandas as pd

def get_parse_color(parse_number):
    color_key = [(20, '#9d9d9d'),
                (50, '#1eff00'),
                (75, '#0070dd'),
                (94, '#a335ee'),
                (100, '#ff8000')]
    
    for colorcode in color_key:
        if parse_number <= colorcode[0]:
            return colorcode[1]
    
    return 'gray'

def make_avg_ilvl_parse_bar_plot(raidnight_object):
    average_parses = []
    for boss_name in raidnight_object.parse_scrapes.keys():
        iparselist = [raidnight_object.parse_scrapes[boss_name][name]['ilvl-performance'] for name in raidnight_object.parse_scrapes[boss_name].keys()]
        average_parse = np.mean(iparselist)
        average_parses.append((average_parse,boss_name))
        
    fig = plt.figure(1)
    ax = fig.add_subplot(111)
    barplot = ax.bar(['\n'.join(wrap(x[1],16)) for x in average_parses], [x[0] for x in average_parses], color=[get_parse_color(x[0]) for x in average_parses], edgecolor='black')
    #plt.xticks(np.arange(len(average_parses)), [x[1] for x in average_parses])
    plt.xticks(rotation=70)
    plt.yticks(np.arange(0,110,10))
    plt.xlabel('Boss')
    plt.tight_layout()
    for a,b in enumerate(x[0] for x in average_parses):
        ax.text(a, b +1, f'{b:{4}.{3}}', color=get_parse_color(b), fontweight='bold', horizontalalignment='center')
    ax.set_facecolor('#A9A9A9')
    fig.set_facecolor('gray')
    plt.show()

def make_heroic_raid_avg_ilvl_parse_scatter_plot(raid_folder):
    average_parses = []

    for filename in [join(raid_folder, f) for f in listdir(raid_folder) if isfile(join(raid_folder, f))]:
        raidnight = Raidnight_Data(filename, 'MyDudes')
        date = pd.to_datetime(datetime.date.fromtimestamp(raidnight.raidnight_date))

        for boss in raidnight.parse_scrapes.keys():
            if not re.search('Heroic', boss):
                continue
            iparselist = [raidnight.parse_scrapes[boss][name]['overall-performance'] for name in raidnight.parse_scrapes[boss].keys() if name=="Bradney"]
            iparse_average = np.mean(iparselist)
            average_parses.append((boss, iparse_average, date))
    
    average_parses = sorted(average_parses, key = lambda x: x[0])

    parse_df = pd.DataFrame(average_parses, columns=["Boss", "Parse", "Date"])
    parse_df.set_index("Date", inplace=True)

    fig = plt.figure(figsize=(15,8))
    ax = fig.add_subplot(111)

    parse_df.groupby('Boss')['Parse'].plot(legend=True, marker='o', linestyle='')

    ax.set_title("Raid Overall Parses by Date")
    ax.set_ylabel("Parse Percentile")
    ax.set_xlabel("Date")
    ordered_handles = {"Heroic Garothi Worldbreaker": 0,
                "Heroic Felhounds of Sargeras": 1,
                "Heroic The Defense of Eonar": 2,
                "Heroic Portal Keeper Hasabel": 3,
                "Heroic Antoran High Command": 4,
                "Heroic Imonar the Soulhunter": 5,
                "Heroic Kin'garoth": 6,
                "Heroic Varimathras": 7,
                "Heroic The Coven of Shivarra": 8,
                "Heroic Aggramar": 9,
                "Heroic Argus the Unmaker": 10}
    
    handles, labels = ax.get_legend_handles_labels()
    handles, labels = zip(*sorted(zip(handles, labels), key=lambda x: ordered_handles[x[1]]))

    ax.legend(handles, labels, bbox_to_anchor=(1.02, 1), loc=2, borderaxespad=0.)
    plt.tight_layout()

    ax.set_yticks(np.arange(0,110,10))

    plt.show()

def make_ilvl_chart(raid_folder, playername=None):
    '''
    defaults to raid average ilvl
    '''
    title_string = "Raid Average Equipped ilvl"
    playerregex = ".*"
    if playername:
        playerregex = playername
        title_string = playername + " Best Equipped ilvl"

    average_parses = []

    for filename in [join(raid_folder, f) for f in listdir(raid_folder) if isfile(join(raid_folder, f))]:
        raidnight = Raidnight_Data(filename, 'MyDudes')
        date = pd.to_datetime(datetime.date.fromtimestamp(raidnight.raidnight_date))
        top_average_ilevel = 0

        for boss in raidnight.damage_done.keys():
            try:
                player_ilevels = [x['itemLevel'] for x in raidnight.damage_done[boss]['entries'] if re.match(playerregex,x['name'])]
            except KeyError:
                continue
            average_ilevel = np.mean(player_ilevels)
            if average_ilevel > top_average_ilevel:
                top_average_ilevel = average_ilevel
        
        if top_average_ilevel != 0:
            average_parses.append((date, top_average_ilevel))
    
    parse_df = pd.DataFrame(average_parses, columns=["Date", "ilevel"])
    parse_df.set_index("Date", inplace=True)

    fig = plt.figure(figsize=(15,8))
    ax = fig.add_subplot(111)
    parse_df["ilevel"].plot(legend=None)

    ax.set_ylabel("ilevel")
    ax.set_title(title_string)

    plt.show()

make_ilvl_chart('MyDudes')