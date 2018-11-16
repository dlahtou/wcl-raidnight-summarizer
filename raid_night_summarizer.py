""" This script is intended to be the base for a comprehensive raid night summarizer """

import datetime
import json
import pprint
import re
import string
from io import BytesIO
from os import listdir
from os.path import isfile, join

import certifi

import pycurl
#from API_keys import wcl_api_key
from get_wcl_api import get_wcl_api_fights, get_wcl_api_table
from scrape_parse_data import scrape_damage_parse_data


## This class holds all information for a raid night
class RaidnightData(object):
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

    API_key = 'bb7a652ddabff076285430d88b002dc8'
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
                    zone_name = '_'.join(RaidnightData.get_zone_name_from_id(self,self.fights['zone']).replace(",","").split(' '))
                    self.raidnight_date = self.fights['start']//1000
                    raidnight_date_string = datetime.date.fromtimestamp(self.raidnight_date).strftime("%y-%m-%d")
                    highest_difficulty = 1
                    for fight in self.fights['fights']:
                        try:
                            if fight['difficulty'] and fight['difficulty'] > highest_difficulty:
                                highest_difficulty = fight['difficulty']
                        except KeyError:
                            pass
                    fight_difficulty_string = RaidnightData.difficulty_dict[highest_difficulty]
                    self.raid_difficulty = fight_difficulty_string
                    self.name = '-'.join([zone_name,fight_difficulty_string,raidnight_date_string])
                return
        
        ## Continue to wcl api for data if no matching filename
        print("Initializing from wcl api...")
        self.wcl_string = initializationdata
        
        ## API call for fights
        report_string = ''.join([self.wcl_string, "?api_key=", RaidnightData.API_key])
        self.fights = get_wcl_api_fights(report_string)
        
        ## gather zone/difficulty/date for name string
        zone_name = '_'.join(RaidnightData.get_zone_name_from_id(self,self.fights['zone']).replace(",","").split(' '))
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
        fight_difficulty_string = RaidnightData.difficulty_dict[highest_difficulty]
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
            temp_fight_name = ' '.join([RaidnightData.difficulty_dict[fight['difficulty']],fight['name']])
            temp_fight_name_with_id = ' '.join([temp_fight_name, str(fight['id'])])
            print(temp_fight_name_with_id)

            ## the common query string in api call for this fight
            fight_api_call_string = ''.join(["/", self.wcl_string,"?start=",str(fight['start_time']),"&end=",str(fight['end_time']),"&api_key=",RaidnightData.API_key])

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
    
    def get_name(self):
        return self.name

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
        raid_name = RaidnightData.get_zone_name_from_id(self, self.fights['zone'])
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

        return ':'.join([str(duration_hours), f'{duration_minutes:02}', f'{duration_seconds:02}'])
    
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
            deathdict_id = ' '.join([RaidnightData.difficulty_dict[fight['difficulty']], fight['name'], str(fight['id'])])
            for entry in self.deaths[deathdict_id]['entries']:
                player_death_list.append(entry['name'])
            nonwipe_deathdict_id = ' '.join([RaidnightData.difficulty_dict[fight['difficulty']], fight['name']])
            nonwipe_deaths_dict[nonwipe_deathdict_id] = player_death_list
        return nonwipe_deaths_dict


def differential_parse_dict(raidnight_object, raid_folder):
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
            if player_name not in combined_prior_parse_dict[boss_diff_and_name].keys():
                continue
            
            this_weeks_overall_parse = this_weeks_parse_dict[boss_diff_and_name][player_name]['overall-performance']
            last_weeks_overall_parse = combined_prior_parse_dict[boss_diff_and_name][player_name]['overall-performance']
            if last_weeks_overall_parse == 0:
                this_weeks_parse_dict[boss_diff_and_name][player_name]['overall-difference'] = 0
            else:
                this_weeks_parse_dict[boss_diff_and_name][player_name]['overall-difference'] = this_weeks_overall_parse - last_weeks_overall_parse

            this_weeks_ilvl_parse = this_weeks_parse_dict[boss_diff_and_name][player_name]['ilvl-performance']
            last_weeks_ilvl_parse = combined_prior_parse_dict[boss_diff_and_name][player_name]['ilvl-performance']

            if last_weeks_ilvl_parse == 0:
                this_weeks_parse_dict[boss_diff_and_name][player_name]['ilvl-difference'] = 0
            else:
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
    parse_dict = differential_parse_dict(raidnight_object, raid_folder)
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
def pretty_time(milliseconds):
    """
    Converts ms to h:mm:ss format

    Parameters:
    milliseconds (int): the duration in ms

    Returns:
    str: an h:mm:ss format string
    """
    seconds = round(milliseconds/1000)
    minutes = str(seconds//60)
    seconds = str(seconds%60)

    return ':'.join([minutes,seconds.zfill(2)])
def pretty_number(psnumber, numbertype):
    if psnumber >= 1000000:
        return "%d.%sM %s" % (psnumber//1000000, str(round((psnumber%1000000)/10000)).zfill(2), numbertype)
    else:
        return f"{round(psnumber/1000, 1)}k  {numbertype}"
def pretty_dps(dps):
    return pretty_number(dps,'DPS')
def pretty_hps(hps):
    return pretty_number(hps,'HPS')

## returns a custom-format report string for the given data
def report_string(raidnight_object, parse_rank_and_data, metric):
    """
    Converts ranked parse data into a human readable string.

    Parameters:
    raidnight_object (RaidnightData): the raidnight corresponding to the parse
    parse_rank_and_data (tuple): (playername, oparse, iparse, bossdiff+name)
    metric (str): type of parse {overall-parse, ilvl-parse, dps, hps}

    Returns:
    str: One full line of human-readable parse info
    """
    pretty_time_str = pretty_time(parse_rank_and_data[-1])
    if metric == 'overall-parse' or metric == 'ilvl-parse':
        pretty_dps_str = pretty_dps(raidnight_object.get_dps(parse_rank_and_data[0], parse_rank_and_data[3]))

    metric_switch = {'overall-parse': lambda x: '{:<17}'.format('(%d) %s' % (x[1], x[0])) + ' -- %s (%s, %s)' % (pretty_dps_str, x[3], pretty_time_str),
                    'ilvl-parse': lambda x: '{:<17}'.format('(%d) %s' % (x[2], x[0])) + ' -- %s (%s, %s)' % (pretty_dps_str, x[3], pretty_time_str),
                    'dps': lambda x: '{:<12}'.format(x[0]) + ' -- %s (%s, %s)' % (pretty_dps(x[1]), x[2], pretty_time_str),
                    'hps': lambda x: '{:<12}'.format(x[0]) + ' -- %s (%s, %s)' % (pretty_hps(x[1]), x[2], pretty_time_str)}

    return metric_switch[metric](parse_rank_and_data)

def dps_report_string(raidnight_object, parse_rank_and_data):
    return report_string(raidnight_object, parse_rank_and_data, 'dps')
def hps_report_string(raidnight_object, parse_rank_and_data):
    return report_string(raidnight_object, parse_rank_and_data, 'hps')
def overall_parse_report_string(raidnight_object, parse_rank_and_data):
    return report_string(raidnight_object, parse_rank_and_data, 'overall-parse')
def ilvl_parse_report_string(raidnight_object, parse_rank_and_data):
    return report_string(raidnight_object, parse_rank_and_data, 'ilvl-parse')

def complete_report(raidnight, raid_folder, report_filename, wcl_string, improved=True):
    raid_difficulty = raidnight.raid_difficulty
    raid_name = raidnight.get_zone_name_from_id(raidnight.fights['zone'])
    raid_date = datetime.date.fromtimestamp(raidnight.raidnight_date).strftime("%A %m/%d/%y")

    report_title = ' '.join([raid_difficulty, raid_name, raid_date])
    with open(report_filename, 'w') as open_file:
        open_file.write('```\n')
        open_file.write(report_title + '\n')
        open_file.write("="*len(report_title) + '\n')

        open_file.write("Raid Week (Lockout Number): %d" % raidnight.get_raid_lockout_period() + '\n')
        open_file.write("Raid Duration: " + raidnight.get_raid_duration() + '\n')

        open_file.write("Bosses Down: " + str(raidnight.get_kill_count()) + '\n')

        open_file.write(f"Wipes: {sum([raidnight.wipes[wipe] for wipe in raidnight.wipes])} total ")
        wipes = []
        for wipe in raidnight.wipes:
            wipes.append(wipe + " " + str(raidnight.wipes[wipe]))
        open_file.write('(' + ', '.join(wipes) + ')')
        
        if improved:
            open_file.write("\n\nMOST IMPROVED ILVL DPS PERFORMANCES:\n")
            for rank, parsedata in enumerate(get_best_ilvl_parse_differential(raidnight,raid_folder,5),1):
                rank = str(rank) + ".) "
                char_name = f'{parsedata[0]:<13}' + "-- +"
                improvement = str(parsedata[1])

                # format to '1.) character   -- +15 (boss) 45->60
                open_file.write(rank + char_name + improvement + " (" + parsedata[2] + ") %d->%d\n" % (parsedata[4],parsedata[3]))

            '''
            open_file.write("\nMOST IMPROVED OVERALL DPS PERFORMANCES:\n")
            for parse_rank_and_data in enumerate(get_best_overall_parse_differential(raidnight,raid_folder,5),1):
                open_file.write(str(parse_rank_and_data[0]) + ".) " + parsedata[0] + ": +" + str(parsedata[1]) + " (" + parsedata[2] + ") %d->%d\n" % (parsedata[4],parsedata[3]))
            ''' # overall performance is largely redundant with ilvl performance

        open_file.write("\nTOP ILVL DPS PERFORMANCES:" + '\n')
        for rank, parsedata in enumerate(get_best_ilvl_parse(raidnight,5),1):
            # write format 1.) character -- 15.0k DPS (boss, 4:00)
            open_file.write(str(rank) + ".) " + ilvl_parse_report_string(raidnight, parsedata) + '\n')

        open_file.write("\nTOP SPEC-WIDE DPS PERFORMANCES:" + '\n')
        for rank, parsedata in enumerate(get_best_overall_parse(raidnight,5),1):
            # write format 1.) character -- 15.0k DPS (boss, 4:00)
            open_file.write(str(rank) + ".) " + overall_parse_report_string(raidnight, parsedata) + '\n')
        
        open_file.write("\nBEST HPS (SINGLE FIGHT):" + '\n')
        for rank, parsedata in enumerate(get_best_hps(raidnight, 5),1):
            # write format 1.) character -- 15.0k HPS (boss, 4:00)
            open_file.write(str(rank) + ".) " + hps_report_string(raidnight, parsedata) + '\n')
        
        open_file.write('```\n')
        open_file.write(f'{raid_date} logs: http://www.warcraftlogs.com/reports/{wcl_string}')

    with open(report_filename, 'r') as open_file:
        print(open_file.read())

## returns a list of raidnight objects in the folder that have the prior week's lockout period
def get_prior_week_data(raidnight, raidfolder):
    raids_list = []
    raid_name = raidnight.raid_name
    for somefile in [f for f in listdir(raidfolder) if isfile(join(raidfolder,f)) and re.search(raid_name, f)]:
        temp_raidnight = RaidnightData(somefile, raidfolder)
        if temp_raidnight.get_raid_lockout_period() + 1 == raidnight.get_raid_lockout_period():
            raids_list.append(temp_raidnight)
    return raids_list
