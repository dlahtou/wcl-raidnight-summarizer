""" This script is intended to be the base for a comprehensive raid night summarizer """

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
from API_keys import wcl_api_key
from get_wcl_api import get_wcl_api_table, get_wcl_api_fights

## This class holds all information for a raid night
class Raidnight_Data(object):
    """This class contains all pertinent data for a raidnight as found on warcraftlogs (wcl)
    Attributes:
        wcl-string: The 16-char alphanumeric identifier for the report on wcl
        name: The unique string with format "zone-difficulty-date" (e.g. "Nighthold-Heroic-05-07-2017")
        fights: The wcl-fights dictionary, containing fight metadata (direct api download)
        damage-done: The aggregate dictionary of wcl damage-done tables (kills only)
            Each damage-done & healing table is entered into the dictionary under the corresponding ID string from fights
        healing: The aggregate dictionary of wcl healing tables (kills only)
        deaths: The aggregate dictionary of wcl deaths tables (kills & wipes)
        parse_scrapes: The aggregate dictionary of wcl damage parse scrapes
        wipes: a dictionary of form {bossname: number}
        raidnight_date: a unix timestamp
        """

    API_key = wcl_api_key()
    difficulty_dict = {1: "Raid-Finder",
                        2: "Flex",
                        3: "Normal",
                        4: "Heroic"}

    def get_zone_name_from_id(self, zoneid):
        with open('zones.json','r') as open_file:
            zones_dict = json.load(open_file)
        for entry in zones_dict:
            if entry['id'] == zoneid:
                return entry['name']

    def __init__(self,initializationdata,raid_folder):
        ## Search working directory for matching filename
        for filename in [join(raid_folder, f) for f in listdir(raid_folder) if isfile(join(raid_folder, f))]:
            if re.search(re.escape(initializationdata),filename):
                with open(filename,'r') as open_file:
                    file_dict = json.load(open_file)
                    self.damage_done = file_dict['damage-done']
                    self.healing = file_dict['healing']
                    self.deaths = file_dict['deaths']
                    self.fights = file_dict['fights']
                    self.wipes = file_dict['wipes']
                    self.parse_scrapes = file_dict['parse-scrapes']
                    self.raidnight_date = file_dict['raidnight-date']
                    self.raid_name = file_dict['raid-name']
                    self.raid_difficulty = file_dict['raid-difficulty']
                return
        
        ## Continue to wcl api for data if no matching filename
        print("Initializing from wcl api...")
        self.wcl_string = initializationdata
        
        ## API call for fights
        report_string = ''.join([self.wcl_string, "?api_key=", Raidnight_Data.API_key])
        self.fights = get_wcl_api_fights(report_string)
        
        ## gather zone/difficulty/date for name string
        zone_name = '_'.join(Raidnight_Data.get_zone_name_from_id(self,self.fights['zone']).replace(",","").split(' '))
        self.raid_name = zone_name
        self.raidnight_date = self.fights['start']//1000
        raidnight_date_string = datetime.date.fromtimestamp(self.raidnight_date).strftime("%y-%m-%d")
        highest_difficulty = 1
        for fight in self.fights['fights']:
            try:
                if fight['difficulty'] and fight['difficulty'] > highest_difficulty:
                    highest_difficulty = fight['difficulty']
            except KeyError:
                pass
        fight_difficulty_string = Raidnight_Data.difficulty_dict[highest_difficulty]
        self.raid_difficulty = fight_difficulty_string
        self.name = '-'.join([zone_name,fight_difficulty_string,raidnight_date_string])
        print(self.name)

        ## initialize wipe dict[bossname]:wipe_amount
        self.wipes = dict()

        ## create dictionaries of raw api call data
        self.damage_done = dict()
        self.healing = dict()
        self.deaths = dict()
        self.parse_scrapes = dict()

        ## add data for each fight under '[difficulty] [bossname]' in appropriate dictionary (for kill-only categories)
                                        ## '[difficulty] [bossname] [number]' for all-pull categories like deaths
        for fight in self.fights['fights']:
            if not fight['boss']:
                continue
            temp_fight_name = ' '.join([Raidnight_Data.difficulty_dict[fight['difficulty']],fight['name']])
            temp_fight_name_with_id = ' '.join([temp_fight_name, str(fight['id'])])
            print(temp_fight_name_with_id)

            ## the common query string in api call for this fight
            fight_api_call_string = ''.join(["/", self.wcl_string,"?start=",str(fight['start_time']),"&end=",str(fight['end_time']),"&api_key=",Raidnight_Data.API_key])

            ## query deaths in fight
            temp_deaths_dict = get_wcl_api_table("deaths"+fight_api_call_string)
            self.deaths[temp_fight_name_with_id] = temp_deaths_dict

            # skip remaining entries for wipes
            if not fight['kill']:
                if temp_fight_name not in self.wipes:
                    self.wipes[temp_fight_name] = 1
                else:
                    self.wipes[temp_fight_name] += 1
                continue

            # scrape parse data from wcl website
            self.parse_scrapes[temp_fight_name] = scrape_damage_parse_data(self.wcl_string,fight['id'])

            # query damage-done and healing
            temp_damage_dict = get_wcl_api_table("damage-done"+fight_api_call_string)
            temp_healing_dict = get_wcl_api_table("healing"+fight_api_call_string)

            self.damage_done[temp_fight_name] = temp_damage_dict
            self.healing[temp_fight_name] = temp_healing_dict

        ## save dictionary to file for later access
        writedict = {'fights': self.fights,
                    'damage-done': self.damage_done,
                    'healing': self.healing,
                    'deaths': self.deaths,
                    'wipes': self.wipes,
                    'parse-scrapes': self.parse_scrapes,
                    'raidnight-date': self.raidnight_date,
                    'raid-name': self.raid_name,
                    'raid-difficulty': self.raid_difficulty}
        with open(join(raid_folder, self.name+'('+initializationdata+').json'),'w') as open_file:
            print("Writing to file...")
            json.dump(writedict,open_file,indent=4)

    def get_fight_time(self, boss_diff_and_name):
        return self.damage_done[boss_diff_and_name]['totalTime'] ## in milliseconds
        
    ## return a set of tuples (playername, dps/hps,[ilvl parse,] bossname, fightduration (ms))
    def get_set(self, set_type):
        return_set = set()
        data_location = {'dps': self.damage_done,
                        'hps': self.healing,
                        'dps_parse': self.parse_scrapes}[set_type]
        
        for boss in data_location:
            fight_time = self.get_fight_time(boss) # in milliseconds
            ## dps/hps format
            if set_type != 'dps_parse':
                for entry in data_location[boss]['entries']:
                    return_set.add((entry['name'],int(entry['total']/fight_time*1000),boss,fight_time))
            ## parses format
            else:
                for entry in data_location[boss].keys():
                    return_set.add((entry,data_location[boss][entry]['overall-performance'],data_location[boss][entry]['ilvl-performance'],boss,fight_time))
        return return_set

    def dps_set(self):
        return self.get_set('dps')
    def hps_set(self):
        return self.get_set('hps')
    def dps_parse_set(self):
        return self.get_set('dps_parse')
    def raid_average_parse_set(self):
        return_set = set()
        for boss in self.parse_scrapes:
            average_overall_parse = sum([self.parse_scrapes[boss][x]['overall-performance'] for x in self.parse_scrapes[boss].keys()])/len(self.parse_scrapes[boss])
            average_ilvl_parse = sum([self.parse_scrapes[boss][x]['ilvl-performance'] for x in self.parse_scrapes[boss].keys()])/len(self.parse_scrapes[boss])
            return_set.add((boss, average_overall_parse, average_ilvl_parse))
        return return_set
    
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
    
    # returns dps for a given player and boss as an int
    def get_dps(self, player_name, boss_diff_and_name):
        fight_duration = self.damage_done[boss_diff_and_name]['totalTime']
        for entry in self.damage_done[boss_diff_and_name]['entries']:
            if entry['name'] == player_name:
                return int(entry['total']/fight_duration*1000)
    
    ## returns the number of weeks since raid release (0 = first normal/heroic week, 1 = first mythic week)
    def get_raid_lockout_period(self):
        with open('raid-release-dates.json','r') as open_file:
            raid_release_timestamps = json.load(open_file)
        raid_name = Raidnight_Data.get_zone_name_from_id(self, self.fights['zone'])
        raid_release_date = raid_release_timestamps[raid_name]
        days_since_release = datetime.date.fromtimestamp(self.raidnight_date) - datetime.date.fromtimestamp(raid_release_date)
        return days_since_release.days//7
    
    def get_raid_duration(self):
        start = datetime.datetime.fromtimestamp(self.fights['start']//1000) #timestamp in ms resolution
        end = datetime.datetime.fromtimestamp(self.fights ['end']//1000)

        duration_timedelta = end - start
        duration_total = duration_timedelta.seconds #in seconds

        duration_hours = duration_total//3600
        duration_minutes = (duration_total%3600)//60
        duration_seconds = duration_total%60

        return ':'.join([str(duration_hours), str(duration_minutes), str(duration_seconds)])
    
    def get_kill_count(self):
        kill_count = 0
        for fight in self.fights['fights']:
            if fight['boss'] and fight['kill']:
                kill_count += 1
        return kill_count
    
    def get_nonwipe_deaths(self):
        ## dict format should be [bossname]: [player1, player2, player3]
        nonwipe_deaths_dict = dict()
        for fight in self.fights['fights']:
            try:
                if fight['kill'] == False:
                    continue
            except KeyError:
                continue
            player_death_list = []
            deathdict_id = ' '.join([Raidnight_Data.difficulty_dict[fight['difficulty']], fight['name'], str(fight['id'])])
            for entry in self.deaths[deathdict_id]['entries']:
                player_death_list.append(entry['name'])
            nonwipe_deathdict_id = ' '.join([Raidnight_Data.difficulty_dict[fight['difficulty']], fight['name']])
            nonwipe_deaths_dict[nonwipe_deathdict_id] = player_death_list
        return nonwipe_deaths_dict


def make_differential_parse_dict(raidnight_object, raid_folder):
    this_weeks_parse_dict = raidnight_object.parse_scrapes
    raids_list = get_prior_week_data(raidnight_object, raid_folder)
    prior_parse_dicts = [f.parse_scrapes for f in raids_list]
    prior_simple_death_dicts = [f.get_nonwipe_deaths() for f in raids_list]
    combined_prior_parse_dict = dict()
    ## add dict entries to combined dict IF player did not die
    for parse_dict,death_dict in zip(prior_parse_dicts, prior_simple_death_dicts):
        for boss in parse_dict.keys():
            if boss not in combined_prior_parse_dict:
                combined_prior_parse_dict[boss] = dict()
            for player in parse_dict[boss].keys():
                if player in death_dict[boss]:
                    continue
                else:
                    combined_prior_parse_dict[boss][player] = parse_dict[boss][player]

    ## update this_weeks_parse_dict with differential values if they exist
    for boss_diff_and_name in this_weeks_parse_dict.keys():
        #skip if boss does not occur in last week's data
        if boss_diff_and_name not in combined_prior_parse_dict.keys():
            continue
        for player_name in this_weeks_parse_dict[boss_diff_and_name].keys():
            ## TODO: pass over values if player died last week
            if player_name not in combined_prior_parse_dict[boss_diff_and_name].keys():
                continue
            
            this_weeks_overall_parse = this_weeks_parse_dict[boss_diff_and_name][player_name]['overall-performance']
            last_weeks_overall_parse = combined_prior_parse_dict[boss_diff_and_name][player_name]['overall-performance']
            this_weeks_parse_dict[boss_diff_and_name][player_name]['overall-difference'] = this_weeks_overall_parse - last_weeks_overall_parse

            this_weeks_ilvl_parse = this_weeks_parse_dict[boss_diff_and_name][player_name]['ilvl-performance']
            last_weeks_ilvl_parse = combined_prior_parse_dict[boss_diff_and_name][player_name]['ilvl-performance']
            this_weeks_parse_dict[boss_diff_and_name][player_name]['ilvl-difference'] = this_weeks_ilvl_parse - last_weeks_ilvl_parse

            this_weeks_parse_dict[boss_diff_and_name][player_name]['last-weeks-overall-performance'] = last_weeks_overall_parse
            this_weeks_parse_dict[boss_diff_and_name][player_name]['last-weeks-ilvl-performance'] = last_weeks_ilvl_parse   

    return this_weeks_parse_dict

## returns a sorted set of tuples representing the best-in-class performance for the raid night
def get_best(raidnight_object, metric, get_amount):
    metric_switch = {'dps': lambda x: sorted(raidnight_object.dps_set(), key=lambda y: y[1], reverse=True)[:x],
                    'overall-parse': lambda x: sorted(raidnight_object.dps_parse_set(), key=lambda y:y[1],reverse=True)[:x],
                    'ilvl-parse': lambda x: sorted(raidnight_object.dps_parse_set(), key=lambda y:y[2],reverse=True)[:x],
                    'hps': lambda x: sorted(raidnight_object.hps_set(), key=lambda y: y[1], reverse=True)[:x],
                    'raid-overall-parse': lambda x: sorted(raidnight_object.raid_average_parse_set(), key = lambda y: y[1], reverse = True)[:x],
                    'raid-ilvl-parse': lambda x: sorted(raidnight_object.raid_average_parse_set(), key=lambda y: y[2], reverse=True)[:x]}
    
    return metric_switch[metric](get_amount)
def get_best_dps(raidnight_object, get_amount):
    return get_best(raidnight_object, 'dps', get_amount)
def get_best_hps(raidnight_object, get_amount):
    return get_best(raidnight_object, 'hps', get_amount)
def get_best_ilvl_parse(raidnight_object, get_amount):
    return get_best(raidnight_object, 'ilvl-parse', get_amount)
def get_best_overall_parse(raidnight_object, get_amount):
    return get_best(raidnight_object, 'overall-parse', get_amount)
def get_best_raid_overall_parse(raidnight_object, get_amount):
    return get_best(raidnight_object, 'raid-overall-parse', get_amount)
def get_best_raid_ilvl_parse(raidnight_object, get_amount):
    return get_best(raidnight_object, 'raid-ilvl-parse', get_amount)
def get_best_parse_differential(raidnight_object, raid_folder, get_amount, parse_type):
    parse_dict = make_differential_parse_dict(raidnight_object, raid_folder)
    overall_difference_set = set()
    for boss in parse_dict.keys():
        for player in parse_dict[boss].keys():
            try:
                overall_difference_set.add((player,parse_dict[boss][player][parse_type + '-difference'],boss,parse_dict[boss][player][parse_type +'-performance'], parse_dict[boss][player]['last-weeks-'+parse_type+'-performance']))
            except KeyError:
                continue
    return sorted(overall_difference_set, key = lambda x: x[1], reverse=True)[:get_amount]
def get_best_overall_parse_differential(raidnight_object, raid_folder, get_amount):
    return get_best_parse_differential(raidnight_object, raid_folder, get_amount, 'overall')
def get_best_ilvl_parse_differential(raidnight_object, raid_folder, get_amount):
    return get_best_parse_differential(raidnight_object, raid_folder, get_amount, 'ilvl')
    

## formatting for output strings
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

def make_complete_report(raidnight, raid_folder, report_filename):
    raid_difficulty = "Heroic"
    raid_name = raidnight.get_zone_name_from_id(raidnight.fights['zone'])
    raid_date = datetime.date.fromtimestamp(raidnight.raidnight_date).strftime("%m/%d/%y")

    report_title = ' '.join([raid_difficulty, raid_name, raid_date])
    with open(report_filename, 'w') as open_file:
        open_file.write(report_title + '\n')
        open_file.write("="*len(report_title) + '\n')

        open_file.write("Raid Week (Lockout Number): %d" % raidnight.get_raid_lockout_period() + '\n')
        open_file.write("Raid Duration: " + raidnight.get_raid_duration() + '\n')

        open_file.write("Bosses Down: " + str(raidnight.get_kill_count()) + '\n')

        open_file.write("\nWIPES: " + '\n')
        for wipe in raidnight.wipes:
            open_file.write(wipe + ": " + str(raidnight.wipes[wipe]) + '\n')
        
        open_file.write("\nTOP ILVL DPS PERFORMANCES:" + '\n')
        for data_tuple in enumerate(get_best_ilvl_parse(raidnight,3),1):
            open_file.write(str(data_tuple[0]) + ".) " + make_ilvl_parse_report_string(raidnight,data_tuple[1]) + '\n')

        open_file.write("\nTOP SPEC-WIDE DPS PERFORMANCES:" + '\n')
        for data_tuple in enumerate(get_best_overall_parse(raidnight,3),1):
            open_file.write(str(data_tuple[0]) + ".) " + make_overall_parse_report_string(raidnight, data_tuple[1]) + '\n')
        
        open_file.write("\nMOST IMPROVED ILVL DPS PERFORMANCES:\n")
        for data_tuple in enumerate(get_best_ilvl_parse_differential(raidnight,raid_folder,5),1):
            open_file.write(str(data_tuple[0]) + ".) " + data_tuple[1][0] + ": +" + str(data_tuple[1][1]) + " (" + data_tuple[1][2] + ") %d->%d\n" % (data_tuple[1][4],data_tuple[1][3]))

        open_file.write("\nMOST IMPROVED OVERALL DPS PERFORMANCES:\n")
        for data_tuple in enumerate(get_best_overall_parse_differential(raidnight,raid_folder,5),1):
            open_file.write(str(data_tuple[0]) + ".) " + data_tuple[1][0] + ": +" + str(data_tuple[1][1]) + " (" + data_tuple[1][2] + ") %d->%d\n" % (data_tuple[1][4],data_tuple[1][3]))

        open_file.write("\nBEST HPS (SINGLE FIGHT):" + '\n')
        for data_tuple in enumerate(get_best_hps(raidnight,3),1):
            open_file.write(str(data_tuple[0]) + ".) " + make_hps_report_string(raidnight, data_tuple[1]) + '\n')

    with open(report_filename, 'r') as open_file:
        print(open_file.read())

## returns a list of raidnight objects in the folder that have the prior week's lockout period
def get_prior_week_data(raidnight, raidfolder):
    raids_list = []
    for somefile in [f for f in listdir(raidfolder) if isfile(join(raidfolder,f))]:
        temp_raidnight = Raidnight_Data(somefile, raidfolder)
        if temp_raidnight.get_raid_lockout_period() + 1 == raidnight.get_raid_lockout_period():
            raids_list.append(temp_raidnight)
    return raids_list

## SANDBOX//TESTING
test = Raidnight_Data('NqTnLRp1bQ7JdaPH', 'MyDudes')
print(test.raid_name)
print("OVERALL PARSE DIFFERENTIALS")
for line in get_best_overall_parse_differential(test, 'MyDudes', 5):
    print(line)
print("ILEVEL PARSE DIFFERENTIALS")
for line in get_best_ilvl_parse_differential(test, 'MyDudes', 5):
    print(line)

raidlist = ['XT26GZHtjQraD4KP','Tncy19zRDZW3GXqY','q6fkh9WcarAPvLKF','KNnmg6yM9WVbv2rP','TGAcPg8V3H7tLCqy','d8DNKx6Yp1hPvmVf']
'''print(listdir('MyDudes'))
for filename in listdir('MyDudes'):
    print(join('MyDudes',filename))
print([join(raid_folder,f) for f in listdir(raid_folder) if isfile(join(raid_folder,f))])'''
for raidstring in raidlist:
    raid_data = Raidnight_Data(raidstring, 'MyDudes')
    print((raidstring, raid_data.get_raid_lockout_period()))
'''test = Raidnight_Data('NqTnLRp1bQ7JdaPH', 'MyDudes')
print(get_best_raid_overall_parse(test,3))
print(get_best_raid_ilvl_parse(test,3))
print(get_best_ilvl_parse(test,3))
make_complete_report(test, 'firstoutputfile.txt')'''