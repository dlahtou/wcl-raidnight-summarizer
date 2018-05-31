""" This program is intended to be the base for a comprehensive raid night summarizer """

import json
import pycurl
import certifi
from io import BytesIO
import string
import datetime

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
        if initializationdata[-5:] == '.json':
            with open(initializationdata,'r') as open_file:
                ## TODO: LATER:define a method or series of instructions to assign data from json
                ## build_from_json(json.load(open_file))
                pass
        elif isinstance(initializationdata,str):
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

            ##TODO: assign tables categories to self.damage-done, self.healing, etc
            self.damage_done = dict()
            self.healing = dict()
            self.deaths = dict()
            for fight in self.fights['fights']:
                temp_fight_name = ' '.join([Raidnight_Data.difficulty_dict[fight['difficulty']],fight['name']])
                temp_fight_name_with_id = ' '.join([temp_fight_name,str(fight['id'])])

                api_curl.setopt(api_curl.URL,''.join([Raidnight_Data.base_tables_url,"deaths","/",self.wcl_string,"?start=",str(fight['start_time']),"&end=",str(fight['end_time']),"&api_key=",Raidnight_Data.API_key]))
                api_return_buffer = BytesIO()
                api_curl.setopt(api_curl.WRITEDATA, api_return_buffer)
                api_curl.perform()
                deaths_json = api_return_buffer.getvalue().decode('utf-8')
                temp_deaths_dict = json.loads(deaths_json)
                self.deaths[temp_fight_name_with_id] = temp_deaths_dict

                if not fight['kill']:
                    continue

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

            with open('raid-night-summarizer-TEST.json','w') as open_file:
                open_file.write(json.dumps(self.deaths,indent=4))
            ## build_from_wcl(initializationdata)
        else:
            raise Exception("invalid initialization data for Raidnight_Data")

test = Raidnight_Data('2fRjG8HcKWhLnXCy')