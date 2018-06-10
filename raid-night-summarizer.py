""" This program is intended to be the base for a comprehensive raid night summarizer """

from os import listdir
from os.path import isfile,join
import json
import pycurl
import certifi
from io import BytesIO
import string
import datetime
import re
import pprint
from scrape_parse_data import scrape_damage_parse_data

def make_pretty_time(milliseconds):
    seconds = round(milliseconds/1000)
    minutes = str(seconds//60)
    seconds = str(seconds%60)
    return ':'.join([minutes,seconds.zfill(2)])

def make_pretty_number(psnumber, numbertype):
    if psnumber >= 1000000:
        return "%d.%sM %s" % (psnumber//1000000, str(round((psnumber%1000000)/10000)).zfill(2), numbertype)
    else:
        return "%dk  %s" % (round(psnumber/1000), numbertype)

def make_pretty_dps(dps):
    return make_pretty_number(dps,'DPS')

def make_pretty_hps(hps):
    return make_pretty_number(hps,'HPS')

## This class holds all information for a raid night
class Raidnight_Data(object):
    base_fights_url = "https://www.warcraftlogs.com:443/v1/report/fights/"
    base_tables_url = "https://www.warcraftlogs.com:443/v1/report/tables/"
    API_key = "bb7a652ddabff076285430d88b002dc8"
    difficulty_dict = {1: "Raid-Finder",
                        2: "Normal",
                        3: "Heroic",
                        4: "Heroic"}

    """This class contains all pertinent data for a raidnight as found on warcraftlogs (wcl)
    Attributes:
        wcl-string: The 16-char alphanumeric identifier for the report on wcl
        name: The unique string with format "zone-difficulty-date" (e.g. "Nighthold-Heroic-05-07-2017")
        fights: The wcl-fights dictionary, containing fight metadata (direct api download)
        damage-done: The aggregate dictionary of wcl damage-done tables (kills only)
            Each damage-done table is entered into the dictionary under the corresponding ID string from fights
        healing: The aggregate dictionary of wcl healing tables (kills only)
        deaths: The aggregate dictionary of wcl deaths tables (kills & wipes)
        +damage-parses: The aggregate dictionary of wcl damage parse scrapes #reachgoal
        +healing-parses: The aggregate dictionary of wcl healing parse scrapes #reachgoal
    """
    def __init__(self,initializationdata):
        ## Search working directory for matching filename
        for filename in [f for f in listdir() if isfile(f)]:
            if re.search(initializationdata,filename):
                print("Initializing from file...")
                with open(filename,'r') as open_file:
                    file_dict = json.load(open_file)
                    self.damage_done = file_dict['damage-done']
                    self.healing = file_dict['healing']
                    self.deaths = file_dict['deaths']
                    self.fights = file_dict['fights']
                    self.wipes = file_dict['wipes']
                    self.parse_data = file_dict['parse-data']
                return
        
        ## Continue to wcl api for data
        print("Initializing from wcl api...")
        self.wcl_string = initializationdata
        
        ## API call for fights
        api_return_buffer = BytesIO()
        api_curl = pycurl.Curl()
        api_curl.setopt(api_curl.URL,''.join([Raidnight_Data.base_fights_url,self.wcl_string,"?api_key=",Raidnight_Data.API_key]))
        api_curl.setopt(api_curl.WRITEDATA, api_return_buffer)
        api_curl.setopt(pycurl.CAINFO, certifi.where())
        api_curl.perform()
        fights_json = api_return_buffer.getvalue().decode('utf-8')
        self.fights = json.loads(fights_json)
        
        ## gather zone/difficulty/date for name string
        with open('zones.json','r') as open_file:
            zones_dict = json.load(open_file)
        for entry in zones_dict:
            if entry['id'] == self.fights['zone']:
                zone_name = '_'.join(entry['name'].replace(",","").split(' '))
                break
        fight_date = datetime.date.fromtimestamp(self.fights['start']//1000).strftime("%y-%m-%d")
        fight_difficulty_string = Raidnight_Data.difficulty_dict[self.fights['fights'][-1]['difficulty']]
        self.name = '-'.join([zone_name,fight_difficulty_string,fight_date])
        print(self.name)

        ## initialize wipe dict[bossname]:wipe_amount
        self.wipes = dict()

        ## create dictionaries of raw api call data
        self.damage_done = dict()
        self.healing = dict()
        self.deaths = dict()
        self.parse_data = dict()

        ## add data for each fight under '[difficulty] [bossname]' in appropriate dictionary (for kill-only categories)
                                        ## '[difficulty] [bossname] [number]' for all-pull categories like deaths
        for fight in self.fights['fights']:
            temp_fight_name = ' '.join([Raidnight_Data.difficulty_dict[fight['difficulty']],fight['name']])
            temp_fight_name_with_id = ' '.join([temp_fight_name, str(fight['id'])])
            print(temp_fight_name_with_id)

            api_curl.setopt(api_curl.URL,''.join([Raidnight_Data.base_tables_url, "deaths", "/", self.wcl_string,"?start=",str(fight['start_time']),"&end=",str(fight['end_time']),"&api_key=",Raidnight_Data.API_key]))
            api_return_buffer = BytesIO()
            api_curl.setopt(api_curl.WRITEDATA, api_return_buffer)
            api_curl.perform()
            deaths_json = api_return_buffer.getvalue().decode('utf-8')
            temp_deaths_dict = json.loads(deaths_json)
            self.deaths[temp_fight_name_with_id] = temp_deaths_dict

            # skip remaining entries for wipes
            if not fight['kill']:
                if temp_fight_name not in self.wipes:
                    self.wipes[temp_fight_name] = 1
                else:
                    self.wipes[temp_fight_name] += 1
                continue

            # scrape parse data from wcl website
            self.parse_data[temp_fight_name] = scrape_damage_parse_data(self.wcl_string,fight['id'])

            # query api for damage-done and healing
            api_curl.setopt(api_curl.URL,''.join([Raidnight_Data.base_tables_url,"damage-done","/",self.wcl_string,"?start=",str(fight['start_time']),"&end=",str(fight['end_time']),"&api_key=",Raidnight_Data.API_key]))
            api_return_buffer = BytesIO()
            api_curl.setopt(api_curl.WRITEDATA, api_return_buffer)
            api_curl.perform()
            damage_json = api_return_buffer.getvalue().decode('utf-8')
            temp_damage_dict = json.loads(damage_json)
            api_curl.setopt(api_curl.URL,''.join([Raidnight_Data.base_tables_url,"healing","/",self.wcl_string,"?start=",str(fight['start_time']),"&end=",str(fight['end_time']),"&api_key=",Raidnight_Data.API_key]))
            api_return_buffer = BytesIO()
            api_curl.setopt(api_curl.WRITEDATA, api_return_buffer)
            api_curl.perform()
            healing_json = api_return_buffer.getvalue().decode('utf-8')
            temp_healing_dict = json.loads(healing_json)

            self.damage_done[temp_fight_name] = temp_damage_dict
            self.healing[temp_fight_name] = temp_healing_dict
        api_curl.close()

        ## save dictionary to file for later access
        writedict = {'fights': self.fights,
                    'damage-done': self.damage_done,
                    'healing': self.healing,
                    'deaths': self.deaths,
                    'wipes': self.wipes,
                    'parse-data': self.parse_data}
        with open(self.name+'('+initializationdata+').json','w') as open_file:
            print("Writing to file...")
            open_file.write(json.dumps(writedict,indent=4))

    def get_fight_time(self, boss_diff_and_name):
        return self.damage_done[boss_diff_and_name]['totalTime']

    ## return a set of tuples (playername, dps/hps, bossname, fightduration (ms))
    def dps_set(self):
        all_dps = set()
        for fight in self.damage_done:
            fight_time = self.damage_done[fight]['totalTime'] # in milliseconds
            for entry in self.damage_done[fight]['entries']:
                all_dps.add((entry['name'],int(entry['total']/fight_time*1000),fight,fight_time))
        return all_dps
    def hps_set(self):
        all_hps = set()
        for fight in self.healing:
            fight_time = self.healing[fight]['totalTime'] # in milliseconds
            for entry in self.healing[fight]['entries']:
                all_hps.add((entry['name'],int(entry['total']/fight_time*1000),fight,fight_time))
        return all_hps
    # dps parses returned as (playername, overallparse, ilvlparse, bossname, fightduration (ms))
    def dps_parse_set(self):
        all_dps_parses = set()
        for fight in self.parse_data:
            fight_time = self.get_fight_time(fight)
            for entry in self.parse_data[fight]:
                all_dps_parses.add((entry['name'],entry['overall-performance'],entry['ilvl-performance'],fight,fight_time))
        return all_dps_parses

    
    # returns a dict[playername]:death_count
    def deaths_dict(self):
        all_deaths = dict()
        for fight in self.deaths:
            for entry in self.deaths[fight]['entries']:
                player_who_died = entry['name']
                if player_who_died not in all_deaths:
                    all_deaths[player_who_died] = 1
                else:
                    all_deaths[player_who_died] += 1
        return all_deaths
    
    def get_wipes(self):
        return self.wipes
    
    def get_parse_data(self):
        return self.parse_data
    
    def get_dps(self, player_name, boss_diff_and_name):
        fight_duration = self.damage_done[boss_diff_and_name]['totalTime']
        for entry in self.damage_done[boss_diff_and_name]['entries']:
            if entry['name'] == player_name:
                return int(entry['total']/fight_duration*1000)
    


test = Raidnight_Data('2fRjG8HcKWhLnXCy')


## returns a sorted set of tuples representing the best-in-class performance for the raid night
def get_best(raidnight_object, metric, get_amount):
    metric_switch = {'dps': lambda x: sorted(raidnight_object.dps_set(), key=lambda y: y[1], reverse=True)[:x],
                    'ilvl-parse': lambda x: sorted(raidnight_object.dps_parse_set(), key=lambda y:y[2],reverse=True)[:x],
                    'overall-parse': lambda x: sorted(raidnight_object.dps_parse_set(), key=lambda y:y[1],reverse=True)[:x],
                    'hps': lambda x: sorted(raidnight_object.hps_set(), key=lambda y: y[1], reverse=True)[:x]}
    
    return metric_switch[metric](get_amount)

def get_best_dps(raidnight_object, get_amount):
    return get_best(raidnight_object, 'dps', get_amount)

def get_best_hps(raidnight_object, get_amount):
    return get_best(raidnight_object, 'hps', get_amount)

def get_best_ilvl_parse(raidnight_object, get_amount):
    return get_best(raidnight_object, 'ilvl-parse', get_amount)

def get_best_overall_parse(raidnight_object, get_amount):
    return get_best(raidnight_object, 'overall-parse', get_amount)

## returns a custom-format report string for the given data
def make_report_string(raidnight_object, data_tuple, metric):
    pretty_time = make_pretty_time(data_tuple[-1])
    if metric == 'overall-parse' or metric == 'ilvl-parse':
        pretty_dps = make_pretty_dps(raidnight_object.get_dps(data_tuple[0], data_tuple[3]))

    metric_switch = {'overall-parse': lambda x: '{:<17}'.format('(%d) %s' % (x[1], x[0])) + ' -- %s (%s, %s)' % (pretty_dps, x[3], pretty_time),
                    'ilvl-parse': lambda x: '{:<17}'.format('(%d) %s' % (x[2], x[0])) + ' -- %s (%s, %s)' % (pretty_dps, x[3], pretty_time),
                    'dps': lambda x: '{:<12}'.format(x[0]) + ' -- %s (%s, %s)' % (make_pretty_dps(x[1]), x[2], pretty_time),
                    'hps': lambda x: '{:<12}'.format(x[0]) + ' -- %s (%s, %s)' % (make_pretty_hps(x[1]), x[2], pretty_time)}

    return metric_switch[metric](data_tuple)

def make_dps_report_string(raidnight_object, data_tuple):
    return make_report_string(raidnight_object, data_tuple, 'dps')
def make_hps_report_string(raidnight_object, data_tuple):
    return make_report_string(raidnight_object, data_tuple, 'hps')
def make_overall_parse_report_string(raidnight_object, data_tuple):
    return make_report_string(raidnight_object, data_tuple, 'overall-parse')
def make_ilvl_parse_report_string(raidnight_object, data_tuple):
    return make_report_string(raidnight_object, data_tuple, 'ilvl-parse')

print("Healing Parses")
for data_tuple in get_best_dps(test,8):
    print(make_dps_report_string(test, data_tuple))
print("Overall Parses:")
for data_tuple in get_best_overall_parse(test,8):
    print(make_overall_parse_report_string(test, data_tuple))
'''for entry in sorted(dps_parse_tuples, key=lambda x:x[1],reverse=True)[:5]:
    print('%s (%d) -- %s (%s, %s)' % (entry[0], entry[1], make_pretty_dps(test.get_dps(entry[0],entry[3])), entry[3], make_pretty_time(test.get_fight_time(entry[3]))))'''
'''dps_tuples = test.dps_set()
pprint.pprint(sorted(dps_tuples, key=lambda x:x[1],reverse=True)[:5],indent=1)
hps_tuples = test.hps_set()
pprint.pprint(sorted(hps_tuples, key=lambda x:x[1],reverse=True)[:5],indent=1)
test_deaths = test.deaths_dict()
pprint.pprint(test_deaths)
print(test.get_wipes())'''